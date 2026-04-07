import chromadb
from api_keys import azure_openai_endpoint, azure_openai_key
from openai import AzureOpenAI

chroma_client = chromadb.PersistentClient(path="./persistent_embeddings_chroma")
chroma_client.heartbeat()

client = AzureOpenAI(
    api_key=azure_openai_key,
    azure_endpoint=azure_openai_endpoint,
    api_version="2025-01-01-preview",
)

EMBEDDING_MODEL = "text-embedding-3-large"  # adjust to your deployment name

def print_results(results):
    """Pretty-print query results."""
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        print(f"\n{'='*80}")
        print(f"Result {i+1} | Distance: {dist:.4f} | Case: {meta.get('case')} | "
              f"Section: {meta.get('section')} | Element: {meta.get('element_id')}")
        print(f"{'='*80}")
        print(doc[:500] + ("..." if len(doc) > 500 else ""))

def query_chromadb(question, collection_name="shopnova_threat_model", n_results=5, where_filter=None):
    """Query ChromaDB with a natural language question."""
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

    results = collection.query(**query_params) #Dictionary unpacking

    return results

if __name__ == "__main__":
    # 3. Test queries
    test_questions = [
        "What threats affect the Customer Database across all cases?",
        "Which mitigations address Denial of Service threats?",
        "What data flows cross the PCI Compliance Zone boundary?",
        "What is the threat-to-mitigation mapping for Transaction Repudiation?",
        "Which elements appear in multiple DFD diagrams?",
    ]

    for q in test_questions:
        print(f"\n{'#'*80}")
        print(f"QUERY: {q}")
        print(f"{'#'*80}")
        results = query_chromadb(q, n_results=3)
        print_results(results)

    # Example: filtered query — only Case 1 chunks
    print(f"\n{'#'*80}")
    print("FILTERED QUERY (Case 1 only): What processes handle payment data?")
    print(f"{'#'*80}")
    results = query_chromadb(
        "What processes handle payment data?",
        n_results=3,
        where_filter={"case": "1"}
    )
    print_results(results)