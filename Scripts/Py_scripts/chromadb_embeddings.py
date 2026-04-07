import chromadb
import re
from openai import AzureOpenAI
from api_keys import azure_openai_endpoint, azure_openai_key
from a_textual_descriptions import text_description

# ─── Azure OpenAI Client ───────────────────────────────────────────────────────

client = AzureOpenAI(
    api_key=azure_openai_key,
    azure_endpoint=azure_openai_endpoint,
    api_version="2025-01-01-preview",
)

EMBEDDING_MODEL = "text-embedding-3-large"  # adjust to your deployment name


# ─── Chunking Strategy ─────────────────────────────────────────────────────────
#
# Two-pass approach:
#   Pass 1 — Split into case-level sections (Case 1 BPMN, Case 1 DFD, etc.)
#   Pass 2 — Within each section, split into element-level chunks using domain
#            patterns (EE, P, DS, DF, T, M, TB identifiers)
#
# Chunks that are too long (>800 tokens ~3200 chars) get a fallback split.
# Chunks that are too short (<80 chars) get merged with the previous chunk.

MAX_CHUNK_CHARS = 3200  # ~800 tokens
MIN_CHUNK_CHARS = 80


def identify_case_and_section(text_block):
    """Extract case number and section type from a text block for metadata."""
    case_match = re.search(r'Case (\d)/5', text_block)
    case_num = int(case_match.group(1)) if case_match else None

    section_type = "unknown"
    if "BPMN Diagram" in text_block[:200]:
        section_type = "bpmn"
    elif "DFD Diagram" in text_block[:200]:
        section_type = "dfd"
    elif "Threat Modeling Diagram" in text_block[:200] or "Threat-to-Mitigation Mapping" in text_block[:200]:
        section_type = "threat_modeling"
    elif "Categorization Diagram" in text_block[:200]:
        section_type = "categorization"
    elif "Threat Categories" in text_block[:200] or "Mitigation Categories" in text_block[:200]:
        section_type = "categorization"

    return case_num, section_type


def split_into_sections(text):
    """Pass 1: Split the full text into case-level sections."""
    # Split on case headers and major section dividers
    # Each case has: BPMN, DFD, Threat Modeling, (optionally) Categorization
    section_pattern = r'(?=(?:Case \d/5|(?:\d+\.\s+(?:BPMN|DFD|Threat Modeling|Threat/Mitigation Categorization))))'
    raw_sections = re.split(section_pattern, text)
    return [s.strip() for s in raw_sections if s.strip() and len(s.strip()) > MIN_CHUNK_CHARS]


def split_section_into_elements(section_text):
    """Pass 2: Split a section into element-level chunks using domain patterns."""
    # Pattern matches element identifiers at the start of a logical block
    # Covers: EE1:, P1:, DS1:, DF1:, T1:, M1:, TB1:, plus section sub-headers
    element_pattern = (
        r'(?=(?:'
        r'EE\d+:.+?Description:|'          # External entities
        r'P\d+:.+?Description:|'            # Processes
        r'DS\d+:.+?Description:|'           # Data stores
        r'DF\d+:.+?Name:|'                  # Data flows
        r'T\d+:.+?Threat Category:|'        # Threats (in threat modeling section)
        r'M\d+:.+?Mitigation Category:|'    # Mitigations (in threat modeling section)
        r'TB\d+:.+?Description:'            # Trust boundaries
        r'))'
    )

    chunks = re.split(element_pattern, section_text)
    chunks = [c.strip() for c in chunks if c.strip()]

    # If no element patterns found, this is likely a BPMN section or intro —
    # return as a single chunk (will be fallback-split if too long)
    if len(chunks) <= 1:
        return [section_text.strip()]

    # The first chunk is the section header/intro before the first element
    # Keep it as context
    return chunks


def fallback_split(text, max_chars=MAX_CHUNK_CHARS, overlap_chars=200):
    """Split oversized chunks by paragraph boundaries with overlap."""
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split('\n')
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 1 > max_chars and current:
            chunks.append(current.strip())
            # Overlap: keep the last portion of the current chunk
            overlap_start = max(0, len(current) - overlap_chars)
            current = current[overlap_start:] + "\n" + para
        else:
            current = current + "\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def merge_small_chunks(chunks, min_chars=MIN_CHUNK_CHARS):
    """Merge chunks that are too small with their predecessor."""
    if not chunks:
        return chunks

    merged = [chunks[0]]
    for chunk in chunks[1:]:
        if len(chunk) < min_chars:
            merged[-1] = merged[-1] + "\n" + chunk
        else:
            merged.append(chunk)
    return merged


def build_chunks(text):
    """Full chunking pipeline: sections → elements → size normalization."""
    sections = split_into_sections(text)
    all_chunks = []

    for section in sections:
        case_num, section_type = identify_case_and_section(section)
        element_chunks = split_section_into_elements(section)
        element_chunks = merge_small_chunks(element_chunks)

        for chunk in element_chunks:
            # Fallback-split any oversized chunks
            sub_chunks = fallback_split(chunk)
            for i, sc in enumerate(sub_chunks):
                # Detect what element type this chunk is about
                element_id = detect_element_id(sc)
                all_chunks.append({
                    "text": sc,
                    "metadata": {
                        "case": case_num,
                        "section": section_type,
                        "element_id": element_id,
                        "chunk_index": len(all_chunks),
                    }
                })

    return all_chunks


def detect_element_id(text):
    """Try to detect the primary element ID referenced in a chunk."""
    # Check for element patterns in order of specificity
    patterns = [
        (r'(EE\d+):', "external_entity"),
        (r'(P\d+):', "process"),
        (r'(DS\d+):', "data_store"),
        (r'(DF\d+):', "data_flow"),
        (r'(T\d+):', "threat"),
        (r'(M\d+):', "mitigation"),
        (r'(TB\d+):', "trust_boundary"),
    ]
    for pattern, etype in patterns:
        match = re.search(pattern, text[:100])  # check start of chunk
        if match:
            return f"{etype}:{match.group(1)}"
    return "section_header"


# ─── Embedding ─────────────────────────────────────────────────────────────────

def get_embeddings(texts, model=EMBEDDING_MODEL):
    """Get embeddings from Azure OpenAI in batches."""
    batch_size = 16  # API limit per call
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(input=batch, model=model)
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)
        print(f"  Embedded batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}")

    return all_embeddings


# ─── ChromaDB Storage ──────────────────────────────────────────────────────────

def store_in_chromadb(chunks, collection_name="shopnova_threat_model"):
    """Store chunks with embeddings in persistent ChromaDB."""
    chroma_client = chromadb.PersistentClient(path="./persistent_embeddings_chroma")
    chroma_client.heartbeat()

    # Delete existing collection if re-running
    try:
        chroma_client.delete_collection(name=collection_name)
        print(f"Deleted existing collection: {collection_name}")
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # cosine similarity
    )

    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    ids = [f"chunk_{i:04d}" for i in range(len(chunks))]

    # Convert metadata values to strings (ChromaDB requirement)
    clean_metadatas = []
    for m in metadatas:
        clean = {}
        for k, v in m.items():
            if v is None:
                clean[k] = "unknown"
            else:
                clean[k] = str(v)
        clean_metadatas.append(clean)

    print(f"\nGenerating embeddings for {len(texts)} chunks...")
    embeddings = get_embeddings(texts)

    print(f"Storing {len(texts)} chunks in ChromaDB...")
    # ChromaDB has a batch limit, insert in batches
    batch_size = 50
    for i in range(0, len(texts), batch_size):
        end = min(i + batch_size, len(texts))
        collection.add(
            ids=ids[i:end],
            documents=texts[i:end],
            embeddings=embeddings[i:end],
            metadatas=clean_metadatas[i:end],
        )

    print(f"Done. Collection '{collection_name}' has {collection.count()} chunks.\n")
    return collection


# ─── Query Function ────────────────────────────────────────────────────────────

def query_chromadb(question, collection_name="shopnova_threat_model", n_results=5, where_filter=None):
    """Query ChromaDB with a natural language question."""
    chroma_client = chromadb.PersistentClient(path="./persistent_embeddings_chroma")
    collection = chroma_client.get_collection(name=collection_name)

    # Embed the query
    response = client.embeddings.create(input=[question], model=EMBEDDING_MODEL)
    query_embedding = response.data[0].embedding

    # Query
    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where_filter:
        query_params["where"] = where_filter

    results = collection.query(**query_params)

    return results


# ─── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 1. Build chunks
    print("Building chunks...")
    chunks = build_chunks(text_description)

    print(f"\nChunking summary:")
    print(f"  Total chunks: {len(chunks)}")
    char_lengths = [len(c["text"]) for c in chunks]
    print(f"  Avg chunk size: {sum(char_lengths) // len(char_lengths)} chars")
    print(f"  Min chunk size: {min(char_lengths)} chars")
    print(f"  Max chunk size: {max(char_lengths)} chars")

    # Show distribution by case and section
    #from collections import Counter
    #case_counts = Counter(c["metadata"]["case"] for c in chunks)
    #section_counts = Counter(c["metadata"]["section"] for c in chunks)
    #element_counts = Counter(c["metadata"]["element_id"].split(":")[0] for c in chunks)
    #print(f"\n  By case: {dict(sorted(case_counts.items()))}")
    #print(f"  By section: {dict(section_counts)}")
    #print(f"  By element type: {dict(element_counts)}")

    # 2. Store in ChromaDB
    collection = store_in_chromadb(chunks)