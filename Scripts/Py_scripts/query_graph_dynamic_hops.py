from openai import AzureOpenAI
from prompts import question_decomposition_prompt, entities_of_interest_extraction_prompt, no_of_hops_choosing_prompt_v3, dfd_automated_sparql_prompt, llm_answer_generation_prompt, transform_context_natural_language_prompt
from api_keys import azure_openai_endpoint, azure_openai_key, azure_gpt41
from ontology import ontology
from pydantic import BaseModel
from typing import Literal
from SPARQLWrapper import SPARQLWrapper, JSON, TURTLE
import time
from questions import questions_truths_list
from cost_tracker import CostTracker
import json

client = AzureOpenAI(api_key=azure_openai_key, azure_endpoint=azure_openai_endpoint, api_version="2025-01-01-preview")

endpoint_url = """http://localhost:7200/repositories/Threat_modeling_v2"""
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
    SELECT ?s ?p ?o ?bo ?bp ?bo2
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

        # only expand URI neighbors, not blank nodes
        if row.get("o", {}).get("type") == "uri" and o != node_uri:
            neighbors.add(o)
        if row.get("s", {}).get("type") == "uri" and s != node_uri:
            neighbors.add(s)

        # collect blank node triples if present
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
    response = client.beta.chat.completions.parse(
        model=azure_gpt41,
        temperature=0,
        seed=123,
        max_tokens=1024,
        response_format=IntentsCollection,
        messages=[
            {"role": "system", "content": question_decomposition_prompt},
            {"role": "user", "content": question}
        ]
    )
    tracker.track(response.usage, "split_intents")
    return response.choices[0].message.parsed.intents

def extract_entities_of_interest(question: str, tracker: CostTracker):
    response = client.beta.chat.completions.parse(
        model=azure_gpt41,
        temperature=0,
        seed=123,
        max_tokens=256,
        response_format=EntitiesOfInterestCollection,
        messages=[
            {"role": "system", "content": entities_of_interest_extraction_prompt},
            {"role": "user", "content": question}
        ]
    )
    tracker.track(response.usage, "entities_of_interest")
    return response.choices[0].message.parsed.entities_of_interest

def find_no_hops(question: str, tracker: CostTracker):
    response = client.beta.chat.completions.parse(
        model=azure_gpt41,
        temperature=0,
        seed=123,
        max_tokens=64,
        response_format=NumberOfHops,
        messages=[
            {"role": "system", "content": no_of_hops_choosing_prompt_v3},
            {"role": "user", "content": question}
        ]
    )
    tracker.track(response.usage, "find_no_hops")
    return response.choices[0].message.parsed.no_hops

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
    #print(query)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.queryAndConvert()
    bindings = result['results']['bindings']
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
    #print(query)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    result = sparql.queryAndConvert()
    bindings = result['results']['bindings']
    if bindings:
        dfd_diagram_uri = bindings[0]["dfd_diagram_uri"]["value"]
        return dfd_diagram_uri
    else:
        return ""

def generate_automated_sparql_query_dfd(question: str, dfd_diagram_uri: str, tracker: CostTracker):
    sparql_query = client.chat.completions.create(
        model=azure_gpt41,
        temperature=0,
        seed=123,
        messages=[
            {"role": "system", "content": dfd_automated_sparql_prompt},
            {"role": "system", "content": "The ontology is: " + ontology},
            {"role": "user", "content": question},
            {"role": "user", "content": "The DFD diagram uri is: " + dfd_diagram_uri}
        ]
    )
    tracker.track(sparql_query.usage, "automated_sparql_generation")
    return sparql_query.choices[0].message.content

def query_dfd(sparql_query: str):
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    result = sparql.queryAndConvert()
    bindings = result['results']['bindings']
    if bindings:
        query_results = ""
        for binding in bindings:
            for key, val in binding.items():
                query_results += f"{key}: {val['value']}\n"
        return query_results
    else:
        return ""

def extract_context_for_question(question: str, tracker: CostTracker):
    contexts = []
    intents = split_user_question_intents(question, tracker)
    #(intents)
    for intent in intents:        
        #Find and extract entities of interest
        entities_of_interest = extract_entities_of_interest(intent, tracker)
        #print(entities_of_interest)
        for entity in entities_of_interest:
            ent_uri, type = find_entity_in_graph(entity)
            #print(type)
            if type != "BPMN Sub-Process":
                #Find number of hops
                no_of_hops = find_no_hops(intent, tracker)
                #print(no_of_hops)
                triples = extract_khop_neighborhood(ent_uri, k=no_of_hops, max_neighbors_per_hop=0)
                context_builder = ""
                for s, p, o in triples:
                    context_builder = context_builder + f"""{s} {p} {o}\n"""
                    #print(s, p, o)
                    #write_file.write(f"""{s} {p} {o}\n""")
                contexts.append(context_builder)
                #write_file.write(str(contexts))
                
                #write_file.close()
            else:
                no_of_hops = -1
                #Extract named graph DFD decomp
                dfd_diagram_uri = extract_linked_dfd(ent_uri)
                #print(dfd_diagram_uri)
                #Use an automated sparql generation function to gather what is needed from the diagram linked to the sub-process
                sparql_query = generate_automated_sparql_query_dfd(intent, dfd_diagram_uri, tracker)
                #print(sparql_query)
                res = query_dfd(sparql_query)
                #print(res)
                contexts.append(res)
    return contexts, no_of_hops

def respond_to_question(question: str, context:list, tracker: CostTracker):
    context_str = str(context)
    response = client.chat.completions.create(
        model=azure_gpt41,
        temperature=0,
        seed=123,
        messages=[
            {"role": "system", "content": llm_answer_generation_prompt},
            {"role": "system", "content": "The context you will rely on is: " + context_str},
            {"role": "user", "content": question}
        ]
    )
    tracker.track(response.usage, "respond_to_question")
    return response.choices[0].message.content

def transform_context_natural_language(context: str):
    context_str = str(context)
    response = client.chat.completions.create(
        model=azure_gpt41,
        temperature=0,
        seed=123,
        messages=[
            {"role": "system", "content": transform_context_natural_language_prompt},
            {"role": "user", "content": "The context you need to transform is: " + context_str}
        ]
    )
    return response.choices[0].message.content

def main():
    #questions_list = [{"""category_id""":"""1""", """question_id""":"""1""", """question""":"""What mitigations are used for the process which outputs the data flow that is taken as input by process "Assess Return Eligibility"?
#""", """ground_truth""": """ground truth"""}]
    #question = """What are the threats affecting process "Screen Review Content"?"""
    #question = """What are the external entities from the "Process Payment" BPMN Sub-Process?"""
    
    questions_ground_truths = []
    rdf_kg_contexts = []

    for question in questions_truths_list:
        print(f"""Processing question: {question["question"]}""")
        tracker = CostTracker(input_price_per_1k=0.002, output_price_per_1k=0.008)
        start = time.time()
        record = {}
        record_kg = {}
        context_for_question, no_hops = extract_context_for_question(question["question"], tracker)
        response = respond_to_question(question["question"], context_for_question, tracker)
        end = time.time()
        total_time = end - start
        #print("####### Question response: \n")
        #print(response)
        #print("\n")
        record["category_id"] = question["category_id"]
        record["question_id"] = question["question_id"]
        record["question"] = question["question"]
        record["response"] = response
        record["ground_truth"] = question["ground_truth"]
        context_natural_language = transform_context_natural_language(context_for_question)
        record["context_natural_language"] = context_natural_language
        record["no_of_hops"] = no_hops
        record["time_elapsed"] = total_time
        record["total_cost"] = tracker.total_cost
        record_kg["context_graph"] = str(context_for_question)
        questions_ground_truths.append(record)
        rdf_kg_contexts.append(record_kg)
    
    file_name = "generated_17_03_demo.json"
    file_particle = "./results"
    filepath = file_particle+f"""/{file_name}"""
    filepath_kg_context = file_particle+f"""/kg_context_{file_name}"""
    write_to_json(filepath, questions_ground_truths)
    write_to_json(filepath_kg_context, rdf_kg_contexts)

if __name__ == "__main__":
    main()

