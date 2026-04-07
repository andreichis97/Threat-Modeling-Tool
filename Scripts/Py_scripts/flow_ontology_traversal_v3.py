"""
Ontology-Guided Path Retrieval — Full Evaluation Pipeline
==========================================================
Integrates iterative ontology traversal with:
- Entity extraction from the full question
- Anchor class resolution via SPARQL
- Per-entity target class/property extraction via LLM + ontology
- Ontology-guided traversal with LLM predicate selection
- SPARQL CONSTRUCT execution
- Answer generation
- Cost tracking and JSON output

No intent splitting — traversal per extracted entity instead.
"""

import json
import time
from dataclasses import dataclass
from typing import Optional, Literal
from SPARQLWrapper import SPARQLWrapper, JSON, TURTLE
from openai import AzureOpenAI
from pydantic import BaseModel

from api_keys import azure_openai_endpoint, azure_openai_key, azure_gpt41
from prompts import (
    entities_of_interest_extraction_prompt_v2,
    llm_answer_generation_prompt,
    llm_predicate_selector_prompt,
    target_extraction_prompt
)
from ontology import ontology
from questions import questions_truths_list_owasp
from cost_tracker import CostTracker

def read_file():
    readFile = open("D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Results//llm_query.txt", "r")
    fileContent = readFile.readlines()
    repository = fileContent[0].strip()
    question = fileContent[2].strip()
    readFile.close()

    return repository, question

def write_file(response):
    writeFile = open("D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Results//query_results.txt", "w")
    writeFile.write(response)
    writeFile.close()


# =============================================================================
# 1. CONFIGURATION
# =============================================================================

ONTOLOGY_GRAPH = "http://www.example.org#Ontology"
PREFIX = "http://www.example.org#"

TRANSPARENT_CLASSES = {"ThreatAssessment", "MitigationAssessment"}

LITERAL_TYPES = {
    "http://www.w3.org/2001/XMLSchema#string",
    "http://www.w3.org/2001/XMLSchema#float",
    "http://www.w3.org/2001/XMLSchema#integer",
    "http://www.w3.org/2001/XMLSchema#boolean",
}

client = AzureOpenAI(
    api_key=azure_openai_key,
    azure_endpoint=azure_openai_endpoint,
    api_version="2025-01-01-preview",
)


# =============================================================================
# 2. PYDANTIC MODELS
# =============================================================================

class EntitiesOfInterestCollection(BaseModel):
    entities_of_interest: list[str]


class PredicateSelection(BaseModel):
    predicate: str
    direction: Literal["forward", "inverse"]
    to: str
    reasoning: str


class TargetExtraction(BaseModel):
    target: str
    target_type: Literal["class", "datatype_property"]
    reasoning: str


# =============================================================================
# 3. TARGET EXTRACTION PROMPT
# =============================================================================

TARGET_EXTRACTION_PROMPT = target_extraction_prompt

# =============================================================================
# 4. HELPER FUNCTIONS
# =============================================================================

def extract_entities_of_interest(question: str, tracker: CostTracker, max_retries=2) -> list[str]:
    """Extract named entities from the full question."""
    for attempt in range(max_retries + 1):
        try:
            response = client.beta.chat.completions.parse(
                model=azure_gpt41,
                temperature=0,
                seed=123,
                max_tokens=1024,
                response_format=EntitiesOfInterestCollection,
                messages=[
                    {"role": "system", "content": entities_of_interest_extraction_prompt_v2},
                    {"role": "user", "content": question},
                ],
            )
            finish = response.choices[0].finish_reason
            if finish != "stop":
                print(f"  WARNING: finish_reason='{finish}' in entities_of_interest (attempt {attempt+1})")
                continue
            tracker.track(response.usage, "entities_of_interest")
            return response.choices[0].message.parsed.entities_of_interest
        except Exception as e:
            print(f"  ERROR in extract_entities_of_interest (attempt {attempt+1}): {e}")
    print(f"  FAILED all retries for entities_of_interest: {question[:80]}")
    return []


def resolve_anchor_class(entity_label: str, sparql_wrapper:SPARQLWrapper) -> Optional[str]:
    """Resolve the rdf:type of an entity by querying the full knowledge graph."""
    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX ex: <{PREFIX}>

    SELECT ?type WHERE {{
        ?anchor_uri rdfs:label "{entity_label}" ;
                    a ?type .
        FILTER(STRSTARTS(STR(?type), "{PREFIX}"))
    }} LIMIT 1
    """
    try:
        sparql_wrapper.setReturnFormat(JSON)
        sparql_wrapper.setQuery(query)
        results = sparql_wrapper.query().convert()
        bindings = results["results"]["bindings"]
        if bindings:
            return bindings[0]["type"]["value"].replace(PREFIX, "")
        return None
    except Exception as e:
        print(f"  ERROR resolving class for '{entity_label}': {e}")
        return None


def extract_target(question: str, entity: str, anchor_class: str,
                   tracker: CostTracker) -> Optional[dict]:
    """Use LLM + ontology to determine the target class or datatype property for a specific entity."""
    user_prompt = f"""QUESTION: {question}

ANCHOR ENTITY: {entity}
ANCHOR CLASS: {anchor_class}

ONTOLOGY:
{ontology}

What is the target that this question is trying to retrieve starting from the entity "{entity}" (a {anchor_class})?"""

    for attempt in range(3):
        try:
            response = client.beta.chat.completions.parse(
                model=azure_gpt41,
                temperature=0,
                seed=123,
                max_tokens=200,
                response_format=TargetExtraction,
                messages=[
                    {"role": "system", "content": TARGET_EXTRACTION_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )

            parsed = response.choices[0].message.parsed
            if parsed is None:
                print(f"  [TARGET] Attempt {attempt+1}: parsed is None, retrying...")
                continue

            tracker.track(response.usage, "extract_target")

            result = {
                "target": parsed.target,
                "target_type": parsed.target_type,
                "reasoning": parsed.reasoning,
            }
            print(f"  [TARGET] {entity} → {result['target']} ({result['target_type']})")
            print(f"  [TARGET] Reason: {result['reasoning']}")
            return result

        except Exception as e:
            print(f"  [TARGET] Attempt {attempt+1} failed: {e}")

    print(f"  [TARGET] All 3 attempts failed for entity '{entity}'.")
    return None


# =============================================================================
# 5. LIVE ONTOLOGY NAVIGATOR
# =============================================================================

class LiveOntologyNavigator:
    """Queries the ontology named graph for valid predicates."""

    def __init__(self, sparql_wrapper:SPARQLWrapper):
        self.sparql = sparql_wrapper
        self.sparql.setReturnFormat(JSON)

    def _query(self, query_str: str) -> list[dict]:
        self.sparql.setQuery(query_str)
        return self.sparql.query().convert()["results"]["bindings"]

    def _strip(self, uri: str) -> str:
        return uri[len(PREFIX):] if uri.startswith(PREFIX) else uri

    def get_forward_predicates(self, current_class: str) -> list[dict]:
        query = f"""
        PREFIX ex: <{PREFIX}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT DISTINCT ?prop ?label ?range WHERE {{
            GRAPH <{ONTOLOGY_GRAPH}> {{
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
            prop_name = self._strip(row["prop"]["value"])
            label = row.get("label", {}).get("value", prop_name)
            range_uri = row["range"]["value"]
            is_literal = range_uri in LITERAL_TYPES
            range_name = self._strip(range_uri) if not is_literal else range_uri.split("#")[-1]

            predicates.append({
                "predicate": prop_name,
                "label": label,
                "range": range_name,
                "is_literal": is_literal,
                "direction": "forward",
            })
        return predicates

    def get_inverse_predicates(self, current_class: str) -> list[dict]:
        query = f"""
        PREFIX ex: <{PREFIX}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

        SELECT DISTINCT ?prop ?label ?domainClass WHERE {{
            GRAPH <{ONTOLOGY_GRAPH}> {{
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
                FILTER(?domainClass != owl:Class)
            }}
        }}
        """
        results = self._query(query)
        predicates = []
        for row in results:
            prop_name = self._strip(row["prop"]["value"])
            label = row.get("label", {}).get("value", prop_name)
            domain_name = self._strip(row["domainClass"]["value"])

            predicates.append({
                "predicate": prop_name,
                "label": label,
                "domain_class": domain_name,
                "direction": "inverse",
            })
        return predicates

    def get_all_candidates(self, current_class: str, target: str,
                           visited_classes: set) -> list[dict]:
        candidates = []

        for pred in self.get_forward_predicates(current_class):
            next_class = pred["range"]
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

        for pred in self.get_inverse_predicates(current_class):
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
# 6. LLM PREDICATE SELECTOR
# =============================================================================

class LLMPredicateSelector:
    """Uses GPT-4.1 to select the best predicate at each traversal step."""

    def __init__(self, tracker: CostTracker):
        self.tracker = tracker
        self.call_count = 0

    def select_predicate(self, question: str, current_class: str,
                         target: str, path_so_far: list,
                         candidates: list) -> Optional[dict]:
        self.call_count += 1

        if path_so_far:
            path_desc = " → ".join(
                f"{s.from_class} --[{s.predicate}]--> {s.to_class}"
                if s.direction == "forward"
                else f"{s.from_class} <--[{s.predicate}]-- {s.to_class}"
                for s in path_so_far
            )
        else:
            path_desc = "(starting position — no steps taken yet)"

        candidates_desc = json.dumps(candidates, indent=2)

        user_prompt = f"""QUESTION: {question}

CURRENT CLASS: {current_class}
TARGET: {target}
PATH SO FAR: {path_desc}

CANDIDATE PREDICATES:
{candidates_desc}

Select the best predicate to move closer to the target "{target}".
Remember: follow the semantics of the question, not just the shortest path."""

        messages = [
            {"role": "system", "content": llm_predicate_selector_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(3):
            try:
                response = client.beta.chat.completions.parse(
                    model=azure_gpt41,
                    temperature=0,
                    seed=123,
                    max_tokens=200,
                    response_format=PredicateSelection,
                    messages=messages,
                )

                parsed = response.choices[0].message.parsed
                if parsed is None:
                    print(f"    [LLM] Attempt {attempt+1}: parsed is None, retrying...")
                    continue

                self.tracker.track(response.usage, "predicate_selection")

                result = {
                    "predicate": parsed.predicate,
                    "direction": parsed.direction,
                    "to": parsed.to,
                    "reasoning": parsed.reasoning,
                }

                print(f"    [LLM] Chose: {result['predicate']} ({result['direction']}) → {result['to']}")
                print(f"    [LLM] Reason: {result['reasoning']}")
                return result

            except Exception as e:
                print(f"    [LLM] Attempt {attempt+1} failed: {e}")

        print(f"    [LLM ERROR] All 3 attempts failed.")
        return None


# =============================================================================
# 7. TRAVERSAL STEP & ENGINE
# =============================================================================

@dataclass
class TraversalStep:
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


class TraversalEngine:
    def __init__(self, navigator: LiveOntologyNavigator,
                 selector: LLMPredicateSelector,
                 max_steps: int = 8):
        self.navigator = navigator
        self.selector = selector
        self.max_steps = max_steps

    def traverse(self, question: str, anchor_entity: str,
                 anchor_class: str, target: str) -> list[TraversalStep]:
        current_class = anchor_class
        visited_classes = {anchor_class}
        path: list[TraversalStep] = []

        print(f"  TRAVERSAL: {anchor_entity} ({anchor_class}) → {target}")

        for step_num in range(self.max_steps):
            if current_class == target:
                print(f"  ✓ TARGET REACHED: {target}")
                break

            # Auto-traverse transparent classes
            if current_class in TRANSPARENT_CLASSES:
                forward = self.navigator.get_forward_predicates(current_class)
                object_props = [p for p in forward if not p["is_literal"]]
                if len(object_props) == 1:
                    pred = object_props[0]
                    step = TraversalStep(pred["predicate"], "forward",
                                        current_class, pred["range"])
                    path.append(step)
                    visited_classes.add(step.to_class)
                    current_class = step.to_class
                    print(f"    [AUTO] Step {step_num+1}: {step}")
                    continue

            candidates = self.navigator.get_all_candidates(
                current_class, target, visited_classes
            )

            if not candidates:
                print(f"  ✗ NO CANDIDATES from {current_class}.")
                break

            # Check for terminal literal
            literal_candidates = [c for c in candidates
                                  if c.get("is_literal") and c["predicate"] == target]
            if literal_candidates:
                step = TraversalStep(target, "forward", current_class,
                                    "LITERAL", is_terminal_literal=True)
                path.append(step)
                print(f"    Step {step_num+1}: {step}")
                print(f"  ✓ LITERAL TARGET REACHED: {target}")
                break

            non_literal = [c for c in candidates if not c.get("is_literal")]
            if not non_literal:
                print(f"  ✗ Only literal predicates from {current_class}.")
                break

            chosen = self.selector.select_predicate(
                question, current_class, target, path, non_literal
            )

            if chosen is None:
                print(f"  ✗ LLM returned no choice at step {step_num+1}.")
                break

            pred_name = chosen["predicate"].replace("ex:", "")
            step = TraversalStep(pred_name, chosen["direction"],
                                 current_class, chosen.get("to", "unknown"))
            path.append(step)
            visited_classes.add(step.to_class)
            current_class = step.to_class
            print(f"    Step {step_num+1}: {step} ({len(non_literal)} candidates)")

        return path


# =============================================================================
# 8. SPARQL BUILDER
# =============================================================================

class TraversalSPARQLBuilder:
    PREFIX_BLOCK = (
        "PREFIX ex: <http://www.example.org#>\n"
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
        "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"
    )

    def build_query(self, anchor_label: str, anchor_class: str,
                    path: list[TraversalStep]) -> str:
        if not path:
            return None

        construct_triples = [
            "?anchor rdfs:label ?anchorLabel .",
            f"?anchor a ex:{anchor_class} .",
        ]
        where_triples = [
            f'?anchor rdfs:label "{anchor_label}" .',
            f"?anchor a ex:{anchor_class} .",
            "?anchor rdfs:label ?anchorLabel .",
        ]

        prev_var = "?anchor"

        for i, step in enumerate(path):
            curr_var = f"?v{i}"
            prop = f"ex:{step.predicate}"

            if step.is_terminal_literal or step.direction == "forward":
                triple = f"{prev_var} {prop} {curr_var} ."
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
# 9. SPARQL EXECUTION
# =============================================================================

def execute_construct(query: str, sparql_wrapper: SPARQLWrapper) -> str:
    """Execute a CONSTRUCT query and return triples as a string."""
    if not query:
        return ""
    try:
        exec_sparql = sparql_wrapper
        exec_sparql.setQuery(query)
        exec_sparql.setReturnFormat(TURTLE)
        result = exec_sparql.query().convert()
        if isinstance(result, bytes):
            return result.decode("utf-8")
        return str(result)
    except Exception as e:
        print(f"  ERROR executing CONSTRUCT: {e}")
        return ""


# =============================================================================
# 10. ANSWER GENERATION
# =============================================================================

def respond_to_question(question: str, context: list, tracker: CostTracker) -> str:
    try:
        context_str = str(context)
        response = client.chat.completions.create(
            model=azure_gpt41,
            temperature=0,
            seed=123,
            messages=[
                {"role": "system", "content": llm_answer_generation_prompt},
                {"role": "system", "content": "The context you will rely on is: " + context_str},
                {"role": "user", "content": question},
            ],
        )
        tracker.track(response.usage, "respond_to_question")
        return response.choices[0].message.content
    except Exception as e:
        print(f"  ERROR in respond_to_question: {e}")
        return ""


# =============================================================================
# 11. SINGLE QUESTION PIPELINE
# =============================================================================

def process_single_question(question_text: str, tracker: CostTracker, sparql_wrapper: SPARQLWrapper) -> tuple[list[str], list[str]]:
    """
    Process a single question:
    1. Extract all entities of interest from the full question
    2. For each entity: resolve class, extract target, traverse, build & execute SPARQL
    3. Concatenate all CONSTRUCT results as context

    Returns:
        (contexts, context_graphs)
    """
    navigator = LiveOntologyNavigator(sparql_wrapper)
    builder = TraversalSPARQLBuilder()
    contexts = []
    context_graphs = []

    # Step 1: Extract entities from the full question
    entities = extract_entities_of_interest(question_text, tracker, max_retries=2)
    if not entities:
        print(f"  WARNING: No entities extracted from question")
        return contexts, context_graphs

    print(f"  Entities extracted: {entities}")

    for entity_idx, entity in enumerate(entities):
        print(f"\n  --- Entity {entity_idx + 1}/{len(entities)}: '{entity}' ---")

        # Step 2: Resolve anchor class via SPARQL
        anchor_class = resolve_anchor_class(entity, sparql_wrapper)
        if not anchor_class:
            print(f"  WARNING: Could not resolve class for '{entity}', skipping")
            continue
        print(f"  Anchor class: {anchor_class}")

        # Step 3: Extract target for this entity
        target_info = extract_target(question_text, entity, anchor_class, tracker)
        if not target_info:
            print(f"  WARNING: Could not extract target for '{entity}', skipping")
            continue

        target = target_info["target"]

        # Step 4: Traverse
        selector = LLMPredicateSelector(tracker)
        engine = TraversalEngine(navigator, selector, max_steps=8)
        path = engine.traverse(question_text, entity, anchor_class, target)

        if not path:
            print(f"  WARNING: Traversal produced empty path for '{entity}'")
            continue

        # Step 5: Build SPARQL
        sparql_query = builder.build_query(entity, anchor_class, path)
        if not sparql_query:
            print(f"  WARNING: No SPARQL generated for '{entity}'")
            continue

        print(f"\n  Generated SPARQL:\n{sparql_query}")

        # Step 6: Execute CONSTRUCT
        graph_result = execute_construct(sparql_query, sparql_wrapper)
        if graph_result:
            contexts.append(graph_result)
            context_graphs.append(graph_result)
            print(f"  ✓ CONSTRUCT returned {len(graph_result)} chars")
        else:
            print(f"  WARNING: CONSTRUCT returned empty result")

    return contexts, context_graphs


# =============================================================================
# 12. MAIN — EVALUATION LOOP
# =============================================================================

def main():
    repository, question = read_file()
    endpoint_url = f"http://localhost:7200/repositories/{repository}"
    sparql_wrapper = SPARQLWrapper(endpoint_url)

    print(f"\n\n{'#'*70}")
    print(f"QUESTION {question[:80]}...")
    print(f"{'#'*70}")

    tracker = CostTracker(input_price_per_1k=0.002, output_price_per_1k=0.008)
    start = time.time()

    try:
        # Extract context via ontology-guided traversal
        contexts, context_graphs = process_single_question(question, tracker, sparql_wrapper)

        # Generate answer
        if contexts:
            response = respond_to_question(question, contexts, tracker)
        else:
            print(f"  WARNING: No context retrieved, answering without context")
            response = respond_to_question(question, ["No context available."], tracker)

        end = time.time()
        total_time = end - start

    except Exception as e:
        end = time.time()
        print(f"  FAILED: {e}")

    # Final write
    write_file(response)
    print(f"\n\n{'='*70}")
    print(f"COMPLETE: Processed the question")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()