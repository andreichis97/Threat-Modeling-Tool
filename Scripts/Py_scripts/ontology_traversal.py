"""
Iterative Ontology-Guided Predicate Selection for SPARQL GraphRAG
==================================================================
LIVE version: queries the actual GraphDB SPARQL endpoint for ontology
structure and uses Azure OpenAI GPT-4.1 for predicate selection.

At each step:
1. Query the ontology graph for valid predicates from the current class
2. Present candidates to the LLM with the full question context
3. LLM selects the best predicate
4. Move to the next class
5. Repeat until target reached
6. Build SPARQL CONSTRUCT from the discovered path
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Literal
from SPARQLWrapper import SPARQLWrapper, JSON
from openai import AzureOpenAI
from api_keys import azure_openai_endpoint, azure_openai_key, azure_gpt41
from prompts import llm_predicate_selector_prompt
from pydantic import BaseModel


# =============================================================================
# 1. CONFIGURATION
# =============================================================================

ENDPOINT_URL = "http://localhost:7200/repositories/Threat_modeling_v2"
ONTOLOGY_GRAPH = "http://www.example.org#Ontology"
PREFIX = "http://www.example.org#"

# Transparent classes — auto-traversed, never valid as final targets
TRANSPARENT_CLASSES = {"ThreatAssessment", "MitigationAssessment"}

# Datatype ranges that indicate literal-valued properties
LITERAL_TYPES = {"http://www.w3.org/2001/XMLSchema#string",
                 "http://www.w3.org/2001/XMLSchema#float",
                 "http://www.w3.org/2001/XMLSchema#integer",
                 "http://www.w3.org/2001/XMLSchema#boolean"}

class PredicateSelection(BaseModel):
    predicate: str
    direction: Literal["forward", "inverse"]
    to: str
    reasoning: str


# =============================================================================
# 2. SPARQL-BASED ONTOLOGY NAVIGATOR
# =============================================================================

class LiveOntologyNavigator:
    """
    Queries the ontology named graph in GraphDB to discover valid predicates
    from/to a given class, handling owl:unionOf domains.
    """

    def __init__(self, endpoint_url: str = ENDPOINT_URL,
                 ontology_graph: str = ONTOLOGY_GRAPH):
        self.sparql = SPARQLWrapper(endpoint_url)
        self.sparql.setReturnFormat(JSON)
        self.ontology_graph = ontology_graph

    def _query(self, query_str: str) -> list[dict]:
        """Execute a SPARQL query and return bindings."""
        self.sparql.setQuery(query_str)
        results = self.sparql.query().convert()
        return results["results"]["bindings"]

    def _strip_prefix(self, uri: str) -> str:
        """Strip the ex: prefix from a URI."""
        if uri.startswith(PREFIX):
            return uri[len(PREFIX):]
        return uri

    def get_forward_predicates(self, current_class: str) -> list[dict]:
        """
        Find all properties where current_class is in the domain
        (either directly or via owl:unionOf).
        Returns list of dicts with: predicate, label, range, is_literal, description
        """
        query = f"""
        PREFIX ex: <{PREFIX}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT DISTINCT ?prop ?label ?range WHERE {{
            GRAPH <{self.ontology_graph}> {{
                ?prop rdfs:domain ?domainSpec .
                ?prop rdfs:range ?range .
                {{
                    FILTER(?domainSpec = ex:{current_class})
                }} UNION {{
                    ?domainSpec owl:unionOf ?list .
                    ?list rdf:rest*/rdf:first ex:{current_class} .
                }}
                OPTIONAL {{ ?prop rdfs:label ?label . }}
            }}
        }}
        """
        results = self._query(query)
        predicates = []
        for row in results:
            prop_uri = row["prop"]["value"]
            prop_name = self._strip_prefix(prop_uri)
            label = row.get("label", {}).get("value", prop_name)
            range_uri = row["range"]["value"]
            is_literal = range_uri in LITERAL_TYPES
            range_name = self._strip_prefix(range_uri) if not is_literal else range_uri.split("#")[-1]

            predicates.append({
                "predicate": prop_name,
                "label": label,
                "range": range_name,
                "is_literal": is_literal,
                "direction": "forward",
            })
        return predicates

    def get_inverse_predicates(self, current_class: str) -> list[dict]:
        """
        Find all object properties where current_class is the range.
        For each, expand the domain (direct or unionOf) to list which
        classes could be reached by traversing this property inversely.
        """
        # First find properties where range = current_class
        query = f"""
        PREFIX ex: <{PREFIX}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT DISTINCT ?prop ?label ?domainClass WHERE {{
            GRAPH <{self.ontology_graph}> {{
                ?prop rdfs:range ex:{current_class} .
                ?prop rdfs:domain ?domainSpec .
                {{
                    BIND(?domainSpec AS ?domainClass)
                    FILTER(isIRI(?domainClass))
                }} UNION {{
                    ?domainSpec owl:unionOf ?list .
                    ?list rdf:rest*/rdf:first ?domainClass .
                    FILTER(isIRI(?domainClass))
                }}
                OPTIONAL {{ ?prop rdfs:label ?label . }}
                # Exclude literal-ranged properties (they can't have class range)
                FILTER(?domainClass != owl:Class)
            }}
        }}
        """
        results = self._query(query)
        predicates = []
        for row in results:
            prop_uri = row["prop"]["value"]
            prop_name = self._strip_prefix(prop_uri)
            label = row.get("label", {}).get("value", prop_name)
            domain_uri = row["domainClass"]["value"]
            domain_name = self._strip_prefix(domain_uri)

            predicates.append({
                "predicate": prop_name,
                "label": label,
                "domain_class": domain_name,
                "direction": "inverse",
            })
        return predicates

    def get_predicate_description(self, predicate_name: str) -> dict:
        """Get full details of a predicate from the ontology."""
        query = f"""
        PREFIX ex: <{PREFIX}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?label ?range WHERE {{
            GRAPH <{self.ontology_graph}> {{
                ex:{predicate_name} rdfs:label ?label .
                ex:{predicate_name} rdfs:range ?range .
            }}
        }}
        """
        results = self._query(query)
        if results:
            return {
                "label": results[0].get("label", {}).get("value", predicate_name),
                "range": self._strip_prefix(results[0]["range"]["value"]),
            }
        return {"label": predicate_name, "range": "unknown"}

    def resolve_entity_class(self, entity_label: str) -> Optional[str]:
        """Look up the rdf:type of an entity by its rdfs:label."""
        query = f"""
        PREFIX ex: <{PREFIX}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT ?type WHERE {{
            ?entity rdfs:label "{entity_label}" .
            ?entity rdf:type ?type .
            FILTER(STRSTARTS(STR(?type), "{PREFIX}"))
        }} LIMIT 1
        """
        results = self._query(query)
        if results:
            return self._strip_prefix(results[0]["type"]["value"])
        return None

    def get_all_candidates(self, current_class: str, target: str,
                           visited_classes: set) -> list[dict]:
        """
        Get all candidate predicates (forward + inverse) from current_class,
        formatted for LLM selection.
        """
        candidates = []

        # Forward predicates
        forward = self.get_forward_predicates(current_class)
        for pred in forward:
            next_class = pred["range"]

            # If it's a literal property, only include if it matches the target
            if pred["is_literal"]:
                if pred["predicate"] == target:
                    candidates.append({
                        "predicate": pred["predicate"],
                        "direction": "forward",
                        "label": pred["label"],
                        "from": current_class,
                        "to": next_class,
                        "is_literal": True,
                    })
                continue

            # Skip loops to visited non-transparent classes
            if next_class in visited_classes and next_class not in TRANSPARENT_CLASSES:
                continue

            candidates.append({
                "predicate": pred["predicate"],
                "direction": "forward",
                "label": pred["label"],
                "from": current_class,
                "to": next_class,
                "is_literal": False,
            })

        # Inverse predicates
        inverse = self.get_inverse_predicates(current_class)
        for pred in inverse:
            domain_class = pred["domain_class"]

            if domain_class in visited_classes and domain_class not in TRANSPARENT_CLASSES:
                continue

            candidates.append({
                "predicate": pred["predicate"],
                "direction": "inverse",
                "label": pred["label"],
                "from": current_class,
                "to": domain_class,
                "is_literal": False,
            })

        return candidates


# =============================================================================
# 3. LLM PREDICATE SELECTOR
# =============================================================================

class LLMPredicateSelector:
    """Uses Azure OpenAI GPT-4.1 to select the best predicate at each step."""

    SYSTEM_PROMPT = llm_predicate_selector_prompt #slightly modify the prompt and use formatted responses

    def __init__(self):
        self.client = AzureOpenAI(
            api_key=azure_openai_key,
            azure_endpoint=azure_openai_endpoint,
            api_version="2025-01-01-preview",
        )
        self.model = azure_gpt41
        self.call_count = 0

    def select_predicate(self, question: str, current_class: str,
                         target: str, path_so_far: list,
                         candidates: list) -> Optional[dict]:
        """Ask GPT-4.1 to select the best predicate from candidates."""
        self.call_count += 1

        # Build path description
        if path_so_far:
            path_desc = " → ".join(
                f"{s.from_class} --[{s.predicate}]--> {s.to_class}"
                if s.direction == "forward"
                else f"{s.from_class} <--[{s.predicate}]-- {s.to_class}"
                for s in path_so_far
            )
        else:
            path_desc = "(starting position — no steps taken yet)"

        # Build candidates description
        candidates_desc = json.dumps(candidates, indent=2)

        user_prompt = f"""QUESTION: {question}

CURRENT CLASS: {current_class}
TARGET: {target}
PATH SO FAR: {path_desc}

CANDIDATE PREDICATES:
{candidates_desc}

Select the best predicate to move closer to the target "{target}".
Remember: follow the semantics of the question, not just the shortest path."""

        for attempt in range(3):
            try:
                response = self.client.chat.completions.parse(
                    model=self.model,
                    response_format=PredicateSelection,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                    max_tokens=200, #use formatted response
                )

                parsed = response.choices[0].message.parsed

                if parsed is None:
                    print(f"    [LLM] Attempt {attempt + 1}: parsed is None, retrying...")
                    continue

                result = {
                    "predicate": parsed.predicate,
                    "direction": parsed.direction,
                    "to": parsed.to,
                    "reasoning": parsed.reasoning,
                }

                print(f"    [LLM] Chose: {result['predicate']} ({result['direction']}) "
                    f"→ {result.get('to', '?')}")
                if result.get("reasoning"):
                    print(f"    [LLM] Reason: {result['reasoning']}")

                return result

            except Exception as e:
                print(f"    [LLM ERROR] {e}")
            print(f"    [LLM ERROR] All 3 attempts failed.")
            return None


# =============================================================================
# 4. TRAVERSAL STEP
# =============================================================================

@dataclass
class TraversalStep:
    """One step in the traversal path."""
    predicate: str
    direction: str
    from_class: str
    to_class: str
    is_terminal_literal: bool = False

    def __repr__(self):
        arrow = "-->" if self.direction == "forward" else "<--"
        if self.is_terminal_literal:
            return f"{self.from_class} {arrow}[{self.predicate}]{arrow} LITERAL"
        return f"{self.from_class} {arrow}[{self.predicate}]{arrow} {self.to_class}"


# =============================================================================
# 5. TRAVERSAL ENGINE
# =============================================================================

class TraversalEngine:
    """
    Iteratively traverses the ontology from anchor class to target.
    Uses live SPARQL queries for ontology discovery and LLM for selection.
    """

    def __init__(self, navigator: LiveOntologyNavigator,
                 selector: LLMPredicateSelector,
                 max_steps: int = 8,
                 auto_traverse_transparent: bool = True):
        self.navigator = navigator
        self.selector = selector
        self.max_steps = max_steps
        self.auto_traverse_transparent = auto_traverse_transparent

    def traverse(self, question: str, anchor_entity: str,
                 anchor_class: str, target: str) -> list[TraversalStep]:
        """
        Perform iterative ontology-guided traversal.
        """
        current_class = anchor_class
        visited_classes = {anchor_class}
        path: list[TraversalStep] = []

        print(f"\n{'='*70}")
        print(f"TRAVERSAL: {anchor_entity} ({anchor_class}) → {target}")
        print(f"Question: {question}")
        print(f"{'='*70}")

        for step_num in range(self.max_steps):
            # Check if we've reached a class target
            if current_class == target:
                print(f"\n✓ TARGET REACHED: {target}")
                break

            # Auto-traverse transparent classes
            if self.auto_traverse_transparent and current_class in TRANSPARENT_CLASSES:
                auto_step = self._auto_traverse_transparent(current_class, path)
                if auto_step:
                    path.append(auto_step)
                    visited_classes.add(auto_step.to_class)
                    current_class = auto_step.to_class
                    print(f"  [AUTO] Step {step_num + 1}: {auto_step}")
                    continue

            # Get candidate predicates from the live ontology
            candidates = self.navigator.get_all_candidates(
                current_class, target, visited_classes
            )

            if not candidates:
                print(f"\n✗ NO CANDIDATES from {current_class}. Traversal stuck.")
                break

            # Check if terminal literal target is directly available
            literal_candidates = [c for c in candidates
                                  if c.get("is_literal") and c["predicate"] == target]
            if literal_candidates:
                step = TraversalStep(
                    predicate=target,
                    direction="forward",
                    from_class=current_class,
                    to_class="LITERAL",
                    is_terminal_literal=True,
                )
                path.append(step)
                print(f"\n  Step {step_num + 1}: {step}")
                print(f"\n✓ LITERAL TARGET REACHED: {target}")
                break

            # Filter to non-literal candidates for class traversal
            non_literal = [c for c in candidates if not c.get("is_literal")]

            if not non_literal:
                print(f"\n✗ Only literal predicates from {current_class}.")
                break

            # Ask LLM to select
            chosen = self.selector.select_predicate(
                question=question,
                current_class=current_class,
                target=target,
                path_so_far=path,
                candidates=non_literal,
            )

            if chosen is None:
                print(f"\n✗ LLM returned no choice at step {step_num + 1}.")
                break

            # Build step
            pred_name = chosen["predicate"].replace("ex:", "")
            direction = chosen["direction"]
            next_class = chosen.get("to", "unknown")

            step = TraversalStep(
                predicate=pred_name,
                direction=direction,
                from_class=current_class,
                to_class=next_class,
            )
            path.append(step)
            visited_classes.add(next_class)
            current_class = next_class

            print(f"\n  Step {step_num + 1}: {step}")
            print(f"    ({len(non_literal)} candidates available)")

        return path

    def _auto_traverse_transparent(self, current_class: str,
                                    path: list) -> Optional[TraversalStep]:
        """Auto-traverse transparent blank node classes."""
        forward = self.navigator.get_forward_predicates(current_class)
        object_props = [p for p in forward if not p["is_literal"]]

        if len(object_props) == 1:
            pred = object_props[0]
            return TraversalStep(
                predicate=pred["predicate"],
                direction="forward",
                from_class=current_class,
                to_class=pred["range"],
            )
        return None


# =============================================================================
# 6. SPARQL BUILDER
# =============================================================================

class TraversalSPARQLBuilder:
    """Builds SPARQL CONSTRUCT from a traversal path."""

    PREFIX_BLOCK = (
        "PREFIX ex: <http://www.example.org#>\n"
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
        "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"
    )

    def build_query(self, anchor_label: str, anchor_class: str,
                    path: list[TraversalStep]) -> str:
        if not path:
            return None

        construct_triples = []
        where_triples = []

        construct_triples.append("?anchor rdfs:label ?anchorLabel .")
        construct_triples.append(f"?anchor a ex:{anchor_class} .")

        where_triples.append(f'?anchor rdfs:label "{anchor_label}" .')
        where_triples.append(f"?anchor a ex:{anchor_class} .")
        where_triples.append("?anchor rdfs:label ?anchorLabel .")

        prev_var = "?anchor"

        for i, step in enumerate(path):
            curr_var = f"?v{i}"
            prop = f"ex:{step.predicate}"

            if step.is_terminal_literal:
                triple = f"{prev_var} {prop} {curr_var} ."
                construct_triples.append(triple)
                where_triples.append(triple)
            elif step.direction == "forward":
                triple = f"{prev_var} {prop} {curr_var} ."
                construct_triples.append(triple)
                where_triples.append(triple)
            else:
                triple = f"{curr_var} {prop} {prev_var} ."
                construct_triples.append(triple)
                where_triples.append(triple)

            if not step.is_terminal_literal and step.to_class not in TRANSPARENT_CLASSES:
                label_var = f"{curr_var}_label"
                construct_triples.append(f"{curr_var} rdfs:label {label_var} .")
                where_triples.append(f"OPTIONAL {{ {curr_var} rdfs:label {label_var} . }}")

            prev_var = curr_var

        construct_block = "\n  ".join(construct_triples)
        where_block = "\n  ".join(where_triples)

        return (
            f"{self.PREFIX_BLOCK}\n"
            f"CONSTRUCT {{\n  {construct_block}\n}}\n"
            f"WHERE {{\n  {where_block}\n}}"
        )


# =============================================================================
# 7. FULL PIPELINE
# =============================================================================

class OntologyGuidedRetriever:
    """Full pipeline: question → traversal → SPARQL → execute → context."""

    def __init__(self, max_steps: int = 8):
        self.navigator = LiveOntologyNavigator()
        self.selector = LLMPredicateSelector()
        self.engine = TraversalEngine(
            navigator=self.navigator,
            selector=self.selector,
            max_steps=max_steps,
        )
        self.builder = TraversalSPARQLBuilder()
        self.sparql_executor = SPARQLWrapper(ENDPOINT_URL)
        self.sparql_executor.setReturnFormat(JSON)

    def retrieve(self, question: str, anchor_entity: str,
                 anchor_class: str, target: str,
                 execute: bool = True) -> dict:
        """
        Full retrieval pipeline.

        Args:
            question: Natural language question
            anchor_entity: Entity label
            anchor_class: RDF class of the anchor (or None to auto-resolve)
            target: Target class or datatype property name
            execute: Whether to execute the SPARQL and return results

        Returns dict with path, sparql, results, and metadata.
        """
        # Auto-resolve class if not provided
        if anchor_class is None:
            anchor_class = self.navigator.resolve_entity_class(anchor_entity)
            if anchor_class is None:
                return {"error": f"Could not resolve class for '{anchor_entity}'"}
            print(f"  [RESOLVED] {anchor_entity} → {anchor_class}")

        # Traverse
        path = self.engine.traverse(question, anchor_entity, anchor_class, target)

        # Build conceptual path
        conceptual = self._conceptual_path(anchor_class, path, target)
        executable = self._executable_path(path)

        # Build SPARQL
        sparql = self.builder.build_query(anchor_entity, anchor_class, path)

        result = {
            "question": question,
            "anchor_entity": anchor_entity,
            "anchor_class": anchor_class,
            "target": target,
            "path": path,
            "conceptual_path": conceptual,
            "executable_path": executable,
            "sparql": sparql,
            "llm_calls": self.selector.call_count,
            "steps": len(path),
        }

        # Execute SPARQL
        if execute and sparql:
            try:
                self.sparql_executor.setQuery(sparql)
                query_results = self.sparql_executor.query().convert()
                result["query_results"] = query_results
                result["result_count"] = len(query_results.get("results", {}).get("bindings", []))
            except Exception as e:
                result["query_error"] = str(e)
                result["result_count"] = 0

        return result

    def _conceptual_path(self, anchor_class: str, path: list[TraversalStep],
                          target: str) -> str:
        classes = [anchor_class]
        for step in path:
            if step.to_class not in TRANSPARENT_CLASSES and step.to_class != "LITERAL":
                classes.append(step.to_class)
            elif step.is_terminal_literal:
                classes.append(f"[{step.predicate}]")
        return " → ".join(classes)

    def _executable_path(self, path: list[TraversalStep]) -> str:
        parts = []
        for step in path:
            arrow = "-->" if step.direction == "forward" else "<--"
            parts.append(f"{step.from_class} {arrow}[{step.predicate}]{arrow} {step.to_class}")
        return "\n  ".join(parts)


# =============================================================================
# 8. MAIN — TEST CASES
# =============================================================================

if __name__ == "__main__":
    retriever = OntologyGuidedRetriever()

    test_cases = [
        {
            "question": "What threats impact the data flows which are outputted by the process 'Execute Payment Transaction'?",
            "anchor_entity": "Execute Payment Transaction",
            "anchor_class": "DFDProcess",
            "target": "Threat",
        },
        {
            "question": "What is the risk level of threats affecting the 'Validate Order' process?",
            "anchor_entity": "Validate Order",
            "anchor_class": "DFDProcess",
            "target": "riskLevel",
        },
        {
            "question": "Which DFD diagram is linked to the 'Process Payment' BPMN subprocess?",
            "anchor_entity": "Process Payment",
            "anchor_class": "BPMNSubProcess",
            "target": "DFDDiagram",
        },
        {
            "question": "What mitigations address threats affecting the 'Customer' external entity?",
            "anchor_entity": "Customer",
            "anchor_class": "DFDExternalEntity",
            "target": "Mitigation",
        },
        {
            "question": "What STRIDE category does the threat 'Payment Data Tampering' belong to?",
            "anchor_entity": "Payment Data Tampering",
            "anchor_class": "Threat",
            "target": "ThreatCategory",
        },
        {
            "question": "Which processes are affected by the threat 'Carrier Identity Spoofing'?",
            "anchor_entity": "Carrier Identity Spoofing",
            "anchor_class": "Threat",
            "target": "DFDProcess",
        },
        {
            "question": "What trust boundary does the 'Validate Payment' process reside in?",
            "anchor_entity": "Validate Payment",
            "anchor_class": "DFDProcess",
            "target": "DFDTrustBoundary",
        },
        {
            "question": "What is the cost value of mitigations applied to the 'Customer Database' data store?",
            "anchor_entity": "Customer Database",
            "anchor_class": "DFDDataStore",
            "target": "costValue",
        },
    ]

    all_results = []

    for i, tc in enumerate(test_cases):
        print(f"\n\n{'#'*70}")
        print(f"TEST CASE {i+1}")
        print(f"{'#'*70}")

        # Reset call counter per test
        retriever.selector.call_count = 0

        result = retriever.retrieve(
            question=tc["question"],
            anchor_entity=tc["anchor_entity"],
            anchor_class=tc["anchor_class"],
            target=tc["target"],
            execute=True,  # Set True when GraphDB is running
        )

        print(f"\n--- RESULT ---")
        print(f"Conceptual path: {result['conceptual_path']}")
        print(f"Executable path:\n  {result['executable_path']}")
        print(f"LLM calls: {result['llm_calls']}")
        print(f"Steps: {result['steps']}")

        if result.get("sparql"):
            print(f"\nGenerated SPARQL:")
            print(result["sparql"])
        else:
            print("\n✗ No SPARQL generated")

        if result.get("result_count") is not None:
            print(f"\nQuery returned {result['result_count']} results")

        all_results.append(result)

    # Summary
    print(f"\n\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    total_llm_calls = 0
    for i, r in enumerate(all_results):
        status = "✓" if r.get("sparql") else "✗"
        llm_calls = r.get("llm_calls", 0)
        total_llm_calls += llm_calls
        print(f"\n{status} [{r['steps']} steps, {llm_calls} LLM calls] "
              f"{r['anchor_entity']} ({r['anchor_class']}) → {r['target']}")
        print(f"  Path: {r['conceptual_path']}")

    print(f"\nTotal LLM calls across all test cases: {total_llm_calls}")

#To implement user question respone function, intents splitting, cost tracking, outputting following the structure of the .json generated results