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

    # ---- name lookup ------------------------------------------------------

    def _find_entity(self, entity_name: str) -> Optional[dict]:
        """
        Find an entity across all loaded files by exact normalised name.
        First file that contains the name wins.
        """
        norm = _normalise_name(entity_name)
        for pf in self.parsed_files:
            if norm in pf["entities"]:
                return pf["entities"][norm]
        return None

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

    def get_entity_info(self, entity_name: str) -> Optional[dict]:
        """
        Look up entity by name, return its full record
        including threats, mitigations, and connected flows.
        """
        entity = self._find_entity(entity_name)
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

    def get_threats_for(self, entity_name: str) -> list[dict]:
        """Return just the threats (with their mitigations) for a named entity."""
        entity = self._find_entity(entity_name)
        if not entity:
            return []
        return entity.get("threats", [])

    def get_mitigations_for(self, entity_name: str) -> list[dict]:
        """Return flattened list of {threat_title, mitigation} pairs."""
        threats = self.get_threats_for(entity_name)
        return [
            {
                "threat_title": t["title"],
                "severity": t["severity"],
                "mitigation": t["mitigation"],
            }
            for t in threats
            if t.get("mitigation")
        ]

    def search(self, entity_name: str) -> list[dict]:
        """
        Find the entity by name and also any entities whose threats
        mention the given name in their title.
        Returns a list of matching entity records.
        """
        norm = _normalise_name(entity_name)
        results = []
        seen = set()

        # Direct name match
        entity = self._find_entity(entity_name)
        if entity:
            results.append(entity)
            seen.add(entity["normalised_name"])

        # Threat-title match: find entities that have a threat whose
        # title contains the query as a substring
        for pf in self.parsed_files:
            for name, rec in pf["entities"].items():
                if name in seen:
                    continue
                for t in rec.get("threats", []):
                    if norm in _normalise_name(t.get("title", "")):
                        results.append(rec)
                        seen.add(name)
                        break

        return results

    # ---- RAGAS context formatter -----------------------------------------

    def extract_context(self, entity_name: str) -> str:
        """
        Given an entity name, produce a single text block
        suitable as 'retrieved context' in a RAGAS evaluation row.

        Tries direct lookup first, then falls back to search
        (which also checks threat titles). Returns empty string
        if nothing found.
        """
        info = self.get_entity_info(entity_name)
        if info:
            return self._format_entity_context(info)

        # Fallback: search (covers threat-title matches)
        hits = self.search(entity_name)
        if not hits:
            return ""

        parts = []
        for rec in hits:
            enriched = dict(rec)
            enriched["connected_flows"] = self.get_connected_flows(rec["name"])
            parts.append(self._format_entity_context(enriched))
        return "\n---\n".join(parts)

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

    def build_ragas_row(self, entity_name: str, question: str, ground_truth: str = "") -> dict:
        """
        Build a single RAGAS evaluation row dict:
            { question, contexts, ground_truth }

        `contexts` is a list with one element (the extracted context string).
        If nothing is found, contexts will be ["No relevant information found."].
        """
        ctx = self.extract_context(entity_name)
        return {
            "question": question,
            "contexts": [ctx if ctx else "No relevant information found."],
            "ground_truth": ground_truth,
        }

    def build_ragas_dataset(
        self, qa_entries: list[dict]
    ) -> list[dict]:
        """
        Given a list of {"entity_name": ..., "question": ..., "ground_truth": ...} dicts,
        return a list of RAGAS-compatible rows with extracted contexts.
        """
        return [
            self.build_ragas_row(
                qa["entity_name"], qa["question"], qa.get("ground_truth", "")
            )
            for qa in qa_entries
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

    # Demo queries — exact entity names
    demo_queries = [
        "Patient Registration Gateway",
        "Electronic Health Records Database",
        "Clinical Audit Trail",
        "Insurance Provider",
        "Patient",
    ]

    for q in demo_queries:
        print(f"\n{'=' * 70}")
        print(f"ENTITY: \"{q}\"")
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

    qa_entries = [
        {
            "entity_name": "Patient Registration Gateway",
            "question": "What threats affect the Patient Registration Gateway?",
            "ground_truth": "Registration Data Tampering, Patient Record Information Disclosure, and Registration Service Denial of Service.",
        },
        {
            "entity_name": "Electronic Health Records Database",
            "question": "How is the EHR Database protected against tampering?",
            "ground_truth": "Clinical Record Versioning with Change Tracking and Database-Level Transparent Data Encryption and Access Auditing.",
        },
        {
            "entity_name": "Insurance Provider",
            "question": "What mitigations exist for spoofing attacks on the Insurance Provider?",
            "ground_truth": "Insurance API Endpoint Certificate Pinning to prevent man-in-the-middle attacks and endpoint impersonation.",
        },
    ]

    rows = idx.build_ragas_dataset(qa_entries)

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