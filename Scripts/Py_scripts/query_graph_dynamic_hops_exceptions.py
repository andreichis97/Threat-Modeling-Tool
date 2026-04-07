from openai import AzureOpenAI
from prompts import (
    question_decomposition_prompt_v2,
    entities_of_interest_extraction_prompt_v2,
    no_of_hops_choosing_prompt_v4,
    dfd_automated_sparql_prompt,
    llm_answer_generation_prompt,
    transform_context_natural_language_prompt,
)
from api_keys import azure_openai_endpoint, azure_openai_key, azure_gpt41
from ontology import ontology
from pydantic import BaseModel
from typing import Literal
from SPARQLWrapper import SPARQLWrapper, JSON, TURTLE
import time
from questions import questions_truths_list_owasp
from cost_tracker import CostTracker
import json

client = AzureOpenAI(
    api_key=azure_openai_key,
    azure_endpoint=azure_openai_endpoint,
    api_version="2025-01-01-preview",
)

endpoint_url = """http://localhost:7200/repositories/Threat_modeling_owasp_medical"""
sparql = SPARQLWrapper(endpoint_url)

class IntentsCollection(BaseModel):
    intents: list[str]

class EntitiesOfInterestCollection(BaseModel):
    entities_of_interest: list[str]

class NumberOfHops(BaseModel):
    no_hops: Literal[0, 1, 2, 3, 4]


def write_to_json(filepath: str, data: list[dict]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_1hop_query(node_uri):
    query = f"""
    SELECT ?s ?p ?o ?bp ?bo ?bo2 ?bo3
    WHERE {{
    {{
        <{node_uri}> ?p ?o .
        BIND(<{node_uri}> AS ?s)
        OPTIONAL {{
            FILTER(isBlank(?o))
            ?o ?bp ?bo .
            OPTIONAL {{
                FILTER(isBlank(?bo))
                ?bo ?bo2 ?bo3 .
            }}
        }}
    }}
    UNION
    {{
        ?s ?p <{node_uri}> .
        BIND(<{node_uri}> AS ?o)
        OPTIONAL {{
            FILTER(isBlank(?s))
            ?s ?bp ?bo .
        }}
    }}
}}"""

    sparql.setQuery(query)
    results = sparql.query().convert()

    triples = set()
    neighbors = set()

    for row in results["results"]["bindings"]:
        s = row["s"]["value"]
        p = row["p"]["value"]
        o = row["o"]["value"]

        triples.add((s, p, o))

        if row.get("o", {}).get("type") == "uri" and o != node_uri:
            neighbors.add(o)
        if row.get("s", {}).get("type") == "uri" and s != node_uri:
            neighbors.add(s)

        if "bp" in row and "bo" in row:
            bp = row["bp"]["value"]
            bo = row["bo"]["value"]
            bnode_subj = o if row["o"]["type"] == "bnode" else s
            triples.add((bnode_subj, bp, bo))
            if row["bo"]["type"] == "uri" and bo != node_uri:
                neighbors.add(bo)

    return triples, neighbors


def extract_khop_neighborhood(start_uri, k, max_neighbors_per_hop=None):
    all_triples = set()
    visited = set()
    frontier = {start_uri}

    for hop in range(k):
        next_frontier = set()

        for node in frontier:
            triples, neighbors = run_1hop_query(node)
            all_triples.update(triples)
            next_frontier.update(neighbors)

        visited.update(frontier)
        next_frontier -= visited

        if max_neighbors_per_hop and len(next_frontier) > max_neighbors_per_hop:
            next_frontier = set(list(next_frontier)[:max_neighbors_per_hop])

        frontier = next_frontier

    return all_triples


def split_user_question_intents(question: str, tracker: CostTracker):
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
            print(f"WARNING: Truncated in split_intents for: {question[:80]}")
            return []
        tracker.track(response.usage, "split_intents")
        return response.choices[0].message.parsed.intents
    except Exception as e:
        print(f"ERROR in split_user_question_intents: {e}")
        return []


def extract_entities_of_interest(question: str, tracker: CostTracker, max_retries=2):
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
                print(f"WARNING: finish_reason='{finish}' in entities_of_interest (attempt {attempt+1})")
                continue
            tracker.track(response.usage, "entities_of_interest")
            return response.choices[0].message.parsed.entities_of_interest
        except Exception as e:
            print(f"ERROR in extract_entities_of_interest (attempt {attempt+1}): {e}")
    print(f"FAILED all retries for entities_of_interest: {question[:80]}")
    return []


def find_no_hops(question: str, tracker: CostTracker, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            response = client.beta.chat.completions.parse(
                model=azure_gpt41,
                temperature=0,
                seed=123,
                max_tokens=64,
                response_format=NumberOfHops,
                messages=[
                    {"role": "system", "content": no_of_hops_choosing_prompt_v4},
                    {"role": "user", "content": question},
                ],
            )
            if response.choices[0].finish_reason == "length":
                print(f"WARNING: Truncated in find_no_hops for: {question[:80]}")
                return 1
            tracker.track(response.usage, "find_no_hops")
            return response.choices[0].message.parsed.no_hops
        except Exception as e:
            print(f"ERROR in find_no_hops: {e}")
            return 1


def find_entity_in_graph(entity_label: str):
    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?entUri ?typeLabel
    WHERE
    {{
        ?entUri rdfs:label ?label ;
            a ?entType .
        FILTER(LCASE(?label) = LCASE("{entity_label}")) 
        ?entType rdfs:label ?typeLabel .
    }}"""
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.queryAndConvert()
    bindings = result["results"]["bindings"]
    if bindings:
        entUri = bindings[0]["entUri"]["value"]
        type = bindings[0]["typeLabel"]["value"]
        return entUri, type
    else:
        return "", ""


def extract_linked_dfd(ent_uri: str):
    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX ex: <http://www.example.org#>
    SELECT ?dfd_diagram_uri
    WHERE
    {{
        <{ent_uri}> ex:hasDfdDecompositionLink ?dfd_diagram_uri .
    }}"""
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.queryAndConvert()
    bindings = result["results"]["bindings"]
    if bindings:
        dfd_diagram_uri = bindings[0]["dfd_diagram_uri"]["value"]
        return dfd_diagram_uri
    else:
        return ""


def generate_automated_sparql_query_dfd(
    question: str, dfd_diagram_uri: str, tracker: CostTracker
):
    try:
        sparql_query = client.chat.completions.create(
            model=azure_gpt41,
            temperature=0,
            seed=123,
            messages=[
                {"role": "system", "content": dfd_automated_sparql_prompt},
                {"role": "system", "content": "The ontology is: " + ontology},
                {"role": "user", "content": question},
                {"role": "user", "content": "The DFD diagram uri is: " + dfd_diagram_uri},
            ],
        )
        tracker.track(sparql_query.usage, "automated_sparql_generation")
        return sparql_query.choices[0].message.content
    except Exception as e:
        print(f"ERROR in generate_automated_sparql_query_dfd: {e}")
        return ""


def query_dfd(sparql_query: str):
    if not sparql_query:
        return ""
    try:
        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        result = sparql.queryAndConvert()
        bindings = result["results"]["bindings"]
        if bindings:
            query_results = ""
            for binding in bindings:
                for key, val in binding.items():
                    query_results += f"{key}: {val['value']}\n"
            return query_results
        else:
            return ""
    except Exception as e:
        print(f"ERROR in query_dfd (likely bad SPARQL): {e}")
        return ""


def extract_context_for_question(question: str, tracker: CostTracker):
    contexts = []
    no_of_hops = 0

    intents = split_user_question_intents(question, tracker)
    if not intents:
        print(f"WARNING: No intents extracted, using original question as single intent")
        intents = [question]

    for intent in intents:
        entities_of_interest = extract_entities_of_interest(intent, tracker, max_retries=2)
        if not entities_of_interest:
            print(f"WARNING: No entities found for intent: {intent[:80]}")
            continue

        for entity in entities_of_interest:
            ent_uri, ent_type = find_entity_in_graph(entity)
            if not ent_uri:
                print(f"WARNING: Entity '{entity}' not found in graph, skipping")
                continue

            if ent_type != "BPMN Sub-Process":
                no_of_hops = find_no_hops(intent, tracker)
                triples = extract_khop_neighborhood(
                    ent_uri, k=no_of_hops, max_neighbors_per_hop=0
                )
                context_builder = ""
                for s, p, o in triples:
                    context_builder += f"{s} {p} {o}\n"
                contexts.append(context_builder)
            else:
                no_of_hops = -1
                dfd_diagram_uri = extract_linked_dfd(ent_uri)
                if not dfd_diagram_uri:
                    print(f"WARNING: No DFD link found for entity '{entity}', skipping")
                    continue
                sparql_query = generate_automated_sparql_query_dfd(
                    intent, dfd_diagram_uri, tracker
                )
                res = query_dfd(sparql_query)
                contexts.append(res)

    return contexts, no_of_hops


def respond_to_question(question: str, context: list, tracker: CostTracker):
    try:
        context_str = str(context)
        response = client.chat.completions.create(
            model=azure_gpt41,
            temperature=0,
            seed=123,
            messages=[
                {"role": "system", "content": llm_answer_generation_prompt},
                {"role": "system", "content": "The context you will rely on is: " + context_str},
                {"role": "user", "content": question}
            ],
        )
        tracker.track(response.usage, "respond_to_question")
        return response.choices[0].message.content
    except Exception as e:
        print(f"ERROR in respond_to_question: {e}")
        return ""


def transform_context_natural_language(context: str):
    try:
        context_str = str(context)
        response = client.chat.completions.create(
            model=azure_gpt41,
            temperature=0,
            seed=123,
            messages=[
                {"role": "system", "content": transform_context_natural_language_prompt},
                {
                    "role": "user",
                    "content": "The context you need to transform is: " + context_str,
                },
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"ERROR in transform_context_natural_language: {e}")
        return ""


def main():
    questions_ground_truths = []
    rdf_kg_contexts = []

    for question in questions_truths_list_owasp:
        print(f"""Processing question: {question["question_id"]} {question["question"]}""")
        try:
            tracker = CostTracker(input_price_per_1k=0.002, output_price_per_1k=0.008)
            start = time.time()

            context_for_question, no_hops = extract_context_for_question(
                question["question"], tracker
            )
            response = respond_to_question(
                question["question"], context_for_question, tracker
            )

            end = time.time()
            total_time = end - start

            context_natural_language = transform_context_natural_language(
                context_for_question
            )

            record = {
                "category_id": question["category_id"],
                "question_id": question["question_id"],
                "question": question["question"],
                "response": response,
                "ground_truth": question["ground_truth"],
                "context_natural_language": context_natural_language,
                "no_of_hops": no_hops,
                "time_elapsed": total_time,
                "total_cost": tracker.total_cost,
            }
            record_kg = {"context_graph": str(context_for_question)}

            questions_ground_truths.append(record)
            rdf_kg_contexts.append(record_kg)

        except Exception as e:
            print(f"FAILED on question {question['question_id']}: {e}")
            questions_ground_truths.append(
                {
                    "category_id": question["category_id"],
                    "question_id": question["question_id"],
                    "question": question["question"],
                    "error": str(e),
                }
            )
            continue

    file_name = "generated_30_03_dynamic_hops_owasp_run3.json"
    file_particle = "./results"
    filepath = file_particle + f"/{file_name}"
    filepath_kg_context = file_particle + f"/kg_context_{file_name}"
    write_to_json(filepath, questions_ground_truths)
    write_to_json(filepath_kg_context, rdf_kg_contexts)


if __name__ == "__main__":
    main()