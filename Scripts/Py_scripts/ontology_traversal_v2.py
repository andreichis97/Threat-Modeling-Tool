"""
Ontology-Guided Path Retrieval — Full Evaluation Pipeline
==========================================================
Integrates iterative ontology traversal with:
- Intent splitting (from dynamic hops pipeline)
- Entity extraction per intent
- Anchor class resolution via SPARQL
- Target class/property extraction via LLM + ontology
- Ontology-guided traversal with LLM predicate selection
- SPARQL CONSTRUCT execution
- Answer generation
- Cost tracking and JSON output
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
    question_decomposition_prompt_v2,
    entities_of_interest_extraction_prompt_v2,
    llm_answer_generation_prompt,
    llm_predicate_selector_prompt,
    target_extraction_prompt
)
from ontology import ontology
from questions import questions_truths_list
from cost_tracker import CostTracker


# =============================================================================
# 1. CONFIGURATION
# =============================================================================

ENDPOINT_URL = "http://localhost:7200/repositories/Threat_modeling_v2"
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

sparql_wrapper = SPARQLWrapper(ENDPOINT_URL)
sparql_wrapper.setReturnFormat(JSON)


# =============================================================================
# 2. PYDANTIC MODELS
# =============================================================================

class IntentsCollection(BaseModel):
    intents: list[str]


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
# 4. HELPER FUNCTIONS (from dynamic hops pipeline)
# =============================================================================

def write_to_json(filepath: str, data: list[dict]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def split_user_question_intents(question: str, tracker: CostTracker) -> list[str]:
    try:
        response = client.beta.chat.completions.parse(
            model=azure_gpt41,
            temperature=0,
            seed=123,
            max_tokens=2048,
            response_format=IntentsCollection,
            messages=[
                {"role": "system", "content": question_decomposition_prompt_v2},
                {"role": "user", "content": question},
            ],
        )
        if response.choices[0].finish_reason == "length":
            print(f"  WARNING: Truncated in split_intents for: {question[:80]}")
            return []
        tracker.track(response.usage, "split_intents")
        return response.choices[0].message.parsed.intents
    except Exception as e:
        print(f"  ERROR in split_user_question_intents: {e}")
        return []


def extract_entities_of_interest(question: str, tracker: CostTracker, max_retries=2) -> list[str]:
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


def resolve_anchor_class(entity_label: str) -> Optional[str]:
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
        sparql_wrapper.setQuery(query)
        results = sparql_wrapper.query().convert()
        bindings = results["results"]["bindings"]
        if bindings:
            type_uri = bindings[0]["type"]["value"]
            return type_uri.replace(PREFIX, "")
        return None
    except Exception as e:
        print(f"  ERROR resolving class for '{entity_label}': {e}")
        return None


def extract_target(question: str, intent: str, tracker: CostTracker) -> Optional[dict]:
    """Use LLM + ontology to determine the target class or datatype property."""
    user_prompt = f"""FULL QUESTION: {question}
CURRENT INTENT: {intent}

ONTOLOGY:
{ontology}

What is the target that this intent is trying to retrieve?"""

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
            print(f"  [TARGET] Extracted: {result['target']} ({result['target_type']})")
            print(f"  [TARGET] Reason: {result['reasoning']}")
            return result

        except Exception as e:
            print(f"  [TARGET] Attempt {attempt+1} failed: {e}")

    print(f"  [TARGET] All 3 attempts failed.")
    return None


# =============================================================================
# 5. LIVE ONTOLOGY NAVIGATOR
# =============================================================================

class LiveOntologyNavigator:
    """Queries the ontology named graph for valid predicates."""

    def __init__(self):
        self.sparql = SPARQLWrapper(ENDPOINT_URL)
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

def execute_construct(query: str) -> str:
    """Execute a CONSTRUCT query and return triples as a string."""
    if not query:
        return ""
    try:
        exec_sparql = SPARQLWrapper(ENDPOINT_URL)
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

def process_single_question(question_text: str, tracker: CostTracker) -> tuple[list[str], list[str]]:
    """
    Process a single question through the ontology-guided traversal pipeline.

    Returns:
        (contexts, context_graphs): lists of context strings and raw CONSTRUCT results
    """
    navigator = LiveOntologyNavigator()
    builder = TraversalSPARQLBuilder()
    contexts = []
    context_graphs = []

    # Step 1: Split intents
    intents = split_user_question_intents(question_text, tracker)
    if not intents:
        print(f"  WARNING: No intents extracted, using original question")
        intents = [question_text]

    for intent_idx, intent in enumerate(intents):
        print(f"\n  --- Intent {intent_idx + 1}/{len(intents)}: {intent[:80]}...")

        # Step 2: Extract entities of interest
        entities = extract_entities_of_interest(intent, tracker, max_retries=2)
        if not entities:
            print(f"  WARNING: No entities found for intent, skipping")
            continue

        # Step 3: Extract target
        target_info = extract_target(question_text, intent, tracker)
        if not target_info:
            print(f"  WARNING: Could not extract target, skipping")
            continue

        target = target_info["target"]

        for entity in entities:
            print(f"\n  Entity: '{entity}'")

            # Step 4: Resolve anchor class
            anchor_class = resolve_anchor_class(entity)
            if not anchor_class:
                print(f"  WARNING: Could not resolve class for '{entity}', skipping")
                continue
            print(f"  Anchor class: {anchor_class}")

            # Step 5: Traverse
            selector = LLMPredicateSelector(tracker)
            engine = TraversalEngine(navigator, selector, max_steps=8)
            path = engine.traverse(intent, entity, anchor_class, target)

            if not path:
                print(f"  WARNING: Traversal produced empty path for '{entity}'")
                continue

            # Step 6: Build SPARQL
            sparql_query = builder.build_query(entity, anchor_class, path)
            if not sparql_query:
                print(f"  WARNING: No SPARQL generated")
                continue

            print(f"\n  Generated SPARQL:\n{sparql_query}")

            # Step 7: Execute CONSTRUCT
            graph_result = execute_construct(sparql_query)
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
    results = []

    for q_idx, question in enumerate(questions_truths_list):
        question_text = question["question"]
        print(f"\n\n{'#'*70}")
        print(f"QUESTION {q_idx + 1}/{len(questions_truths_list)}: {question_text[:80]}...")
        print(f"Category: {question['category_id']} | ID: {question['question_id']}")
        print(f"{'#'*70}")

        tracker = CostTracker(input_price_per_1k=0.002, output_price_per_1k=0.008)
        start = time.time()

        try:
            # Extract context via ontology-guided traversal
            contexts, context_graphs = process_single_question(question_text, tracker)

            # Generate answer
            response = ""
            if contexts:
                response = respond_to_question(question_text, contexts, tracker)
            else:
                print(f"  WARNING: No context retrieved, answering without context")
                response = respond_to_question(question_text, ["No context available."], tracker)

            end = time.time()
            total_time = end - start

            record = {
                "category_id": question["category_id"],
                "question_id": question["question_id"],
                "question": question_text,
                "response": response,
                "ground_truth": question["ground_truth"],
                "context_graph": "\n---\n".join(context_graphs) if context_graphs else "",
                "time_elapsed": total_time,
                "total_cost": tracker.total_cost,
            }

            results.append(record)
            print(f"\n  ✓ Done in {total_time:.2f}s | Cost: ${tracker.total_cost:.6f}")
            print(f"  Response: {response[:150]}...")

            # Write after each question for crash recovery
            write_to_json("./results/generated_ontology_traversal.json", results)

        except Exception as e:
            end = time.time()
            print(f"  FAILED: {e}")
            results.append({
                "category_id": question["category_id"],
                "question_id": question["question_id"],
                "question": question_text,
                "response": "",
                "ground_truth": question["ground_truth"],
                "context_graph": "",
                "time_elapsed": end - start,
                "total_cost": tracker.total_cost,
                "error": str(e),
            })
            write_to_json("./results/generated_ontology_traversal.json", results)
            continue

    # Final write
    write_to_json("./results/generated_26_03_ontology_traversal_run1.json", results)
    print(f"\n\n{'='*70}")
    print(f"COMPLETE: Processed {len(results)} questions")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()