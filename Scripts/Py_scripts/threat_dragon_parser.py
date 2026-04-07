"""
OWASP Threat Dragon JSON Parser & Extractor

Parses Threat Dragon diagram exports and extracts threat model information
by entity name matching. Supports multi-file search with fallback.

Designed to produce structured context for RAGAS evaluation pipelines,
where this flat-file extraction approach is compared against a knowledge graph.
"""

import json
import re
from typing import Optional
from difflib import SequenceMatcher


# ---------------------------------------------------------------------------
# 1. PARSING — build a normalised index from raw Threat Dragon JSON
# ---------------------------------------------------------------------------

# Threat Dragon entity types mapped to human-readable categories
ENTITY_TYPES = {
    "tm.Actor": "actor",
    "tm.Process": "process",
    "tm.Store": "store",
    "tm.Flow": "flow",
    "tm.BoundaryBox": "trust_boundary",
}


def _normalise_name(name: str) -> str:
    """Lowercase, strip whitespace/newlines for matching."""
    return re.sub(r"\s+", " ", name).strip().lower()


def parse_threat_dragon_file(filepath: str) -> dict:
    """
    Parse a single Threat Dragon JSON file into a structured index.

    Returns:
        {
            "meta": { title, version },
            "entities": { normalised_name: entity_record, ... },
            "id_to_name": { cell_uuid: normalised_name, ... },
            "flows": [ flow_records ],
        }
    """
    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    meta = {
        "title": raw.get("summary", {}).get("title", ""),
        "version": raw.get("version", ""),
        "source_file": filepath,
    }

    entities: dict = {}
    id_to_name: dict = {}
    flows: list = []

    for diagram in raw.get("detail", {}).get("diagrams", []):
        diagram_title = diagram.get("title", "")
        diagram_type = diagram.get("diagramType", "")

        for cell in diagram.get("cells", []):
            data = cell.get("data", {})
            raw_type = data.get("type", "")
            category = ENTITY_TYPES.get(raw_type)
            if category is None:
                continue

            raw_name = data.get("name", "")
            norm_name = _normalise_name(raw_name)
            cell_id = cell.get("id", "")

            # --- Build the entity record --------------------------------
            record = {
                "name": raw_name.strip(),
                "normalised_name": norm_name,
                "category": category,
                "description": (data.get("description") or "").strip(),
                "cell_id": cell_id,
                "diagram": diagram_title,
                "diagram_type": diagram_type,
                "source_file": filepath,
            }

            # Category-specific attributes
            if category == "trust_boundary":
                record["is_trust_boundary"] = data.get("isTrustBoundary", False)

            if category == "actor":
                record["provides_authentication"] = data.get("providesAuthentication", False)
                record["out_of_scope"] = data.get("outOfScope", False)

            if category == "process":
                record["handles_card_payment"] = data.get("handlesCardPayment", False)
                record["is_web_application"] = data.get("isWebApplication", False)
                record["privilege_level"] = data.get("privilegeLevel", "")
                record["out_of_scope"] = data.get("outOfScope", False)

            if category == "store":
                record["is_a_log"] = data.get("isALog", False)
                record["is_encrypted"] = data.get("isEncrypted", False)
                record["is_signed"] = data.get("isSigned", False)
                record["stores_credentials"] = data.get("storesCredentials", False)
                record["out_of_scope"] = data.get("outOfScope", False)

            if category == "flow":
                record["is_bidirectional"] = data.get("isBidirectional", False)
                record["is_encrypted"] = data.get("isEncrypted", False)
                record["is_public_network"] = data.get("isPublicNetwork", False)
                record["protocol"] = data.get("protocol", "")
                record["out_of_scope"] = data.get("outOfScope", False)
                record["source_cell_id"] = cell.get("source", {}).get("cell", "")
                record["target_cell_id"] = cell.get("target", {}).get("cell", "")

            # Threats
            raw_threats = data.get("threats", [])
            record["threats"] = [
                {
                    "title": t.get("title", ""),
                    "type": t.get("type", ""),           # STRIDE category
                    "status": t.get("status", ""),
                    "severity": t.get("severity", ""),
                    "score": t.get("score", ""),
                    "description": t.get("description", ""),
                    "mitigation": t.get("mitigation", ""),
                }
                for t in raw_threats
            ]
            record["has_open_threats"] = data.get("hasOpenThreats", False)
            record["threat_frequency"] = data.get("threatFrequency", {})

            # Store in index
            entities[norm_name] = record
            if cell_id:
                id_to_name[cell_id] = norm_name

            # Collect flows separately for relationship resolution
            if category == "flow":
                flows.append(record)

    # --- Resolve flow source/target names --------------------------------
    for flow in flows:
        src_id = flow.get("source_cell_id", "")
        tgt_id = flow.get("target_cell_id", "")
        flow["source_entity"] = id_to_name.get(src_id, src_id)
        flow["target_entity"] = id_to_name.get(tgt_id, tgt_id)

    return {
        "meta": meta,
        "entities": entities,
        "id_to_name": id_to_name,
        "flows": flows,
    }


# ---------------------------------------------------------------------------
# 2. MULTI-FILE INDEX — merge multiple parsed files with source tracking
# ---------------------------------------------------------------------------

class ThreatDragonIndex:
    """
    Holds parsed data from 1..N Threat Dragon JSON files.
    Lookup is done in file-load order: first match wins,
    but the caller can also request a merged view.
    """

    def __init__(self):
        self.parsed_files: list[dict] = []  # ordered list of parse results
        self.all_entity_names: set[str] = set()

    def load(self, filepath: str):
        parsed = parse_threat_dragon_file(filepath)
        self.parsed_files.append(parsed)
        self.all_entity_names.update(parsed["entities"].keys())

    # ---- name matching ----------------------------------------------------

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    @staticmethod
    def _acronym_of(text: str) -> str:
        """Build an acronym from the first letter of each word."""
        return "".join(w[0] for w in text.split() if w).lower()

    @staticmethod
    def _query_words(text: str) -> set[str]:
        return set(text.lower().split())

    def _find_entity(
        self, query: str, threshold: float = 0.50
    ) -> Optional[dict]:
        """
        Find an entity across all loaded files by name.
        Strategy:
          1. Exact normalised match (first file wins)
          2. Substring containment — prefer the most specific match
             (= highest overlap ratio between query and candidate)
          3. Acronym match (e.g. "EHR" → "Electronic Health Records")
          4. Word-overlap scoring
          5. Fuzzy similarity above threshold
        """
        norm_q = _normalise_name(query)
        q_words = self._query_words(norm_q)

        # Pass 1 — exact
        for pf in self.parsed_files:
            if norm_q in pf["entities"]:
                return pf["entities"][norm_q]

        # Pass 2 — substring containment, ranked by specificity
        # We score by: len(overlap) / max(len(query), len(name))
        # so "patient registration gateway" matching itself scores higher
        # than "patient" matching "patient registration gateway"
        substring_candidates = []
        for pf in self.parsed_files:
            for name, rec in pf["entities"].items():
                if norm_q in name or name in norm_q:
                    overlap = min(len(norm_q), len(name))
                    specificity = overlap / max(len(norm_q), len(name))
                    substring_candidates.append((specificity, rec))
        if substring_candidates:
            substring_candidates.sort(key=lambda x: x[0], reverse=True)
            return substring_candidates[0][1]

        # Pass 3 — acronym match
        # Check if query words contain an acronym that matches an entity
        for pf in self.parsed_files:
            for name, rec in pf["entities"].items():
                entity_acronym = self._acronym_of(name)
                # Does the query contain this entity's acronym as a word?
                for qw in q_words:
                    if qw == entity_acronym and len(qw) >= 2:
                        return rec
                # Or is the entire query an acronym of the entity?
                q_as_acronym = norm_q.replace(" ", "")
                if q_as_acronym == entity_acronym and len(q_as_acronym) >= 2:
                    return rec

        # Pass 4 — word overlap scoring
        best_overlap, best_rec = 0.0, None
        for pf in self.parsed_files:
            for name, rec in pf["entities"].items():
                name_words = self._query_words(name)
                if not name_words or not q_words:
                    continue
                intersection = q_words & name_words
                if intersection:
                    # Jaccard-like but weighted towards query coverage
                    score = len(intersection) / len(q_words)
                    if score > best_overlap:
                        best_overlap, best_rec = score, rec
        if best_overlap >= 0.4:
            return best_rec

        # Pass 5 — fuzzy
        best_score, best_rec = 0.0, None
        for pf in self.parsed_files:
            for name, rec in pf["entities"].items():
                s = self._similarity(norm_q, name)
                if s > best_score:
                    best_score, best_rec = s, rec
        if best_score >= threshold:
            return best_rec
        return None

    def _find_entities_multi(
        self, query: str, threshold: float = 0.45
    ) -> list[dict]:
        """Return ALL entities whose name partially matches the query."""
        norm_q = _normalise_name(query)
        results = []
        seen = set()
        for pf in self.parsed_files:
            for name, rec in pf["entities"].items():
                if name in seen:
                    continue
                if (
                    norm_q in name
                    or name in norm_q
                    or self._similarity(norm_q, name) >= threshold
                ):
                    results.append(rec)
                    seen.add(name)
        return results

    # ---- relationship helpers --------------------------------------------

    def get_connected_flows(self, entity_name: str) -> list[dict]:
        """Get all flows where this entity is source or target."""
        norm = _normalise_name(entity_name)
        results = []
        for pf in self.parsed_files:
            for flow in pf["flows"]:
                if flow["source_entity"] == norm or flow["target_entity"] == norm:
                    results.append(flow)
        return results

    def get_trust_boundary_for(self, entity_name: str) -> Optional[dict]:
        """Attempt to find the trust boundary an entity sits inside."""
        entity = self._find_entity(entity_name)
        if not entity:
            return None
        # Heuristic: check boundary boxes whose description mentions the entity
        norm = _normalise_name(entity_name)
        for pf in self.parsed_files:
            for name, rec in pf["entities"].items():
                if rec["category"] == "trust_boundary":
                    if norm in _normalise_name(rec["description"]):
                        return rec
        return None

    # ---- high-level extraction methods -----------------------------------

    def get_entity_info(self, query: str) -> Optional[dict]:
        """
        Primary lookup: find entity by name, return its full record
        including threats, mitigations, and connected flows.
        """
        entity = self._find_entity(query)
        if not entity:
            return None

        # Enrich with relationships
        result = dict(entity)
        result["connected_flows"] = self.get_connected_flows(entity["name"])
        boundary = self.get_trust_boundary_for(entity["name"])
        result["trust_boundary"] = (
            {"name": boundary["name"], "description": boundary["description"]}
            if boundary
            else None
        )
        return result

    def get_threats_for(self, query: str) -> list[dict]:
        """Return just the threats (with their mitigations) for a named entity."""
        entity = self._find_entity(query)
        if not entity:
            return []
        return entity.get("threats", [])

    def get_mitigations_for(self, query: str) -> list[dict]:
        """Return flattened list of {threat_title, mitigation} pairs."""
        threats = self.get_threats_for(query)
        return [
            {
                "threat_title": t["title"],
                "severity": t["severity"],
                "mitigation": t["mitigation"],
            }
            for t in threats
            if t.get("mitigation")
        ]

    def search(self, query: str) -> list[dict]:
        """
        Broad search: match the query against entity names AND threat titles.
        Returns a list of relevant entity records.
        """
        norm_q = _normalise_name(query)
        results = []
        seen = set()

        # Name match
        for rec in self._find_entities_multi(query):
            key = rec["normalised_name"]
            if key not in seen:
                results.append(rec)
                seen.add(key)

        # Threat-title match
        for pf in self.parsed_files:
            for name, rec in pf["entities"].items():
                if name in seen:
                    continue
                for t in rec.get("threats", []):
                    if norm_q in _normalise_name(t.get("title", "")):
                        results.append(rec)
                        seen.add(name)
                        break

        return results

    # ---- RAGAS context formatter -----------------------------------------

    # Words to strip from natural language queries to isolate entity names
    _STOP_WORDS = {
        "what", "which", "who", "how", "is", "are", "does", "do", "the",
        "a", "an", "for", "of", "in", "on", "to", "and", "or", "with",
        "that", "this", "by", "from", "its", "their", "there", "be",
        "been", "being", "was", "were", "has", "have", "had", "can",
        "could", "would", "should", "will", "shall", "may", "might",
        "threats", "threat", "mitigations", "mitigation", "affect",
        "affects", "associated", "related", "describe", "explain",
        "list", "tell", "me", "about", "against", "exist", "exists",
        "protected", "attacks", "attack", "what's",
    }

    def _preprocess_query(self, query: str) -> list[str]:
        """
        Extract candidate search terms from a natural language question.
        Returns a list of progressively shorter candidate strings to try:
          1. The full query as-is
          2. The query with stop words removed
          3. Individual multi-word entity name candidates (longest first)
        """
        candidates = [query]

        # Strip stop words to get core terms
        words = _normalise_name(query).split()
        core = [w for w in words if w not in self._STOP_WORDS]
        if core and core != words:
            candidates.append(" ".join(core))

        # Also try contiguous subsequences of core words (longest first)
        # This helps when the query is e.g. "threats for Patient Registration Gateway"
        # and core = ["patient", "registration", "gateway"]
        if len(core) >= 2:
            for length in range(len(core), 1, -1):
                for start in range(len(core) - length + 1):
                    sub = " ".join(core[start : start + length])
                    if sub not in candidates:
                        candidates.append(sub)

        return candidates

    def extract_context(self, query: str) -> str:
        """
        Given a natural-language query, produce a single text block
        suitable as 'retrieved context' in a RAGAS evaluation row.

        The method tries (in order):
          1. Direct entity lookup by name (with query preprocessing)
          2. Broad search across names + threat titles
          3. Returns empty string if nothing found
        """
        # Try progressively stripped versions of the query
        for candidate in self._preprocess_query(query):
            info = self.get_entity_info(candidate)
            if info:
                return self._format_entity_context(info)

        # Fallback: broad search on core terms
        for candidate in self._preprocess_query(query):
            hits = self.search(candidate)
            if hits:
                parts = []
                for rec in hits:
                    enriched = dict(rec)
                    enriched["connected_flows"] = self.get_connected_flows(rec["name"])
                    parts.append(self._format_entity_context(enriched))
                return "\n---\n".join(parts)

        return ""

    @staticmethod
    def _format_entity_context(entity: dict) -> str:
        """Format a single entity record into readable context text."""
        lines = []
        lines.append(f"Entity: {entity['name']}")
        lines.append(f"Type: {entity['category']}")
        lines.append(f"Diagram: {entity.get('diagram', '')}")
        lines.append(f"Source File: {entity.get('source_file', '')}")

        if entity.get("description"):
            lines.append(f"Description: {entity['description']}")

        # Category-specific flags
        flags = []
        for flag_key in [
            "provides_authentication", "out_of_scope", "handles_card_payment",
            "is_web_application", "is_a_log", "is_encrypted", "is_signed",
            "stores_credentials", "is_bidirectional", "is_public_network",
            "is_trust_boundary",
        ]:
            val = entity.get(flag_key)
            if val is True:
                flags.append(flag_key.replace("_", " "))
        if entity.get("privilege_level"):
            flags.append(f"privilege_level={entity['privilege_level']}")
        if entity.get("protocol"):
            flags.append(f"protocol={entity['protocol']}")
        if flags:
            lines.append(f"Properties: {', '.join(flags)}")

        # Trust boundary
        tb = entity.get("trust_boundary")
        if tb:
            lines.append(f"Trust Boundary: {tb['name']} — {tb['description']}")

        # Threats
        threats = entity.get("threats", [])
        if threats:
            lines.append(f"Threats ({len(threats)}):")
            for i, t in enumerate(threats, 1):
                lines.append(
                    f"  [{i}] {t['title']} (type={t['type']}, "
                    f"severity={t['severity']}, score={t['score']}, "
                    f"status={t['status']})"
                )
                lines.append(f"      Description: {t['description']}")
                if t.get("mitigation"):
                    lines.append(f"      Mitigation: {t['mitigation']}")

        # Connected flows
        flows = entity.get("connected_flows", [])
        if flows:
            lines.append(f"Connected Data Flows ({len(flows)}):")
            for fl in flows:
                direction = "→"
                if fl.get("source_entity") == entity.get("normalised_name"):
                    peer = fl.get("target_entity", "?")
                    direction = f"{entity['name']} → {peer}"
                else:
                    peer = fl.get("source_entity", "?")
                    direction = f"{peer} → {entity['name']}"
                lines.append(f"  - {fl['name']}: {direction}")
                if fl.get("description"):
                    lines.append(f"    ({fl['description']})")

        return "\n".join(lines)

    # ---- RAGAS integration ------------------------------------------------

    def build_ragas_row(self, question: str, ground_truth: str = "") -> dict:
        """
        Build a single RAGAS evaluation row dict:
            { question, contexts, ground_truth }

        `contexts` is a list with one element (the extracted context string).
        If nothing is found, contexts will be ["No relevant information found."].
        """
        ctx = self.extract_context(question)
        return {
            "question": question,
            "contexts": [ctx if ctx else "No relevant information found."],
            "ground_truth": ground_truth,
        }

    def build_ragas_dataset(
        self, qa_pairs: list[dict]
    ) -> list[dict]:
        """
        Given a list of {"question": ..., "ground_truth": ...} dicts,
        return a list of RAGAS-compatible rows with extracted contexts.
        """
        return [
            self.build_ragas_row(qa["question"], qa.get("ground_truth", ""))
            for qa in qa_pairs
        ]

    # ---- introspection ---------------------------------------------------

    def list_all_entities(self) -> list[dict]:
        """Return a summary list of all entities across loaded files."""
        result = []
        seen = set()
        for pf in self.parsed_files:
            for name, rec in pf["entities"].items():
                if name in seen:
                    continue
                seen.add(name)
                result.append({
                    "name": rec["name"],
                    "category": rec["category"],
                    "threat_count": len(rec.get("threats", [])),
                    "has_open_threats": rec.get("has_open_threats", False),
                    "source_file": rec.get("source_file", ""),
                })
        return result


# ---------------------------------------------------------------------------
# 3. CLI / demo usage
# ---------------------------------------------------------------------------

def demo():
    """Quick demo showing how to use the parser."""
    import sys
    import os

    files = sys.argv[1:] if len(sys.argv) > 1 else []
    if not files:
        # Default to the uploaded sample
        default = "/mnt/user-data/uploads/Case2_Patient_Admission.json"
        if os.path.exists(default):
            files = [default]
        else:
            print("Usage: python threat_dragon_parser.py <file1.json> [file2.json ...]")
            sys.exit(1)

    idx = ThreatDragonIndex()
    for f in files:
        idx.load(f)
        print(f"Loaded: {f}")

    print(f"\nTotal entities: {len(idx.list_all_entities())}\n")

    # Print entity summary
    print("=" * 70)
    print("ENTITY INDEX")
    print("=" * 70)
    for e in idx.list_all_entities():
        tag = f"[{e['category'].upper()}]"
        threats_tag = f"  ({e['threat_count']} threats)" if e['threat_count'] else ""
        print(f"  {tag:20s} {e['name']}{threats_tag}")

    # Demo queries
    demo_queries = [
        "Patient Registration Gateway",
        "EHR Database",
        "Clinical Audit Trail",
        "Insurance Provider",
        "spoofing",
    ]

    for q in demo_queries:
        print(f"\n{'=' * 70}")
        print(f"QUERY: \"{q}\"")
        print("=" * 70)
        ctx = idx.extract_context(q)
        if ctx:
            print(ctx[:2000])
            if len(ctx) > 2000:
                print(f"\n... (truncated, full length: {len(ctx)} chars)")
        else:
            print("  No results found.")


def ragas_demo():
    """Show how to produce RAGAS-compatible evaluation rows."""
    import os

    default = "/mnt/user-data/uploads/Case2_Patient_Admission.json"
    if not os.path.exists(default):
        print("Sample file not found.")
        return

    idx = ThreatDragonIndex()
    idx.load(default)

    # Example QA pairs (you'd typically load these from your eval set)
    qa_pairs = [
        {
            "question": "What threats affect the Patient Registration Gateway?",
            "ground_truth": "Registration Data Tampering, Patient Record Information Disclosure, and Registration Service Denial of Service.",
        },
        {
            "question": "How is the EHR Database protected against tampering?",
            "ground_truth": "Clinical Record Versioning with Change Tracking and Database-Level Transparent Data Encryption and Access Auditing.",
        },
        {
            "question": "What mitigations exist for spoofing attacks on the Insurance Provider?",
            "ground_truth": "Insurance API Endpoint Certificate Pinning to prevent man-in-the-middle attacks and endpoint impersonation.",
        },
    ]

    rows = idx.build_ragas_dataset(qa_pairs)

    print("=" * 70)
    print("RAGAS DATASET PREVIEW")
    print("=" * 70)
    for i, row in enumerate(rows):
        print(f"\n--- Row {i+1} ---")
        print(f"Question:     {row['question']}")
        print(f"Ground Truth: {row['ground_truth']}")
        ctx_preview = row["contexts"][0][:300]
        print(f"Context:      {ctx_preview}...")
        print()


if __name__ == "__main__":
    import sys
    if "--ragas" in sys.argv:
        ragas_demo()
    else:
        demo()