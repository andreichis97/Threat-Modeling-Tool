from api_keys import openai_api_key
import os
from SPARQLWrapper import SPARQLWrapper, JSON
from openai import OpenAI
import tiktoken

os.environ["OPENAI_API_KEY"] = openai_api_key
client = OpenAI()

def read_file():
    readFile = open("D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Results//llm_query.txt", "r")
    fileContent = readFile.readlines()
    repository = fileContent[0].strip()
    query = fileContent[2].strip()
    readFile.close()

    return repository, query

def write_file(response):
    writeFile = open("D://Andrei//ModellingTools//Threat_Modeling_Tool//Scripts//Results//query_results.txt", "w")
    writeFile.write(response)
    writeFile.close()

def query_GraphDB(repository):

    #repository = "threat_modeling"
    # Set the endpoint URL of the graph database server
    endpoint_url = f"""http://localhost:7200/repositories/{repository}"""

    # Create a new SPARQLWrapper instance
    sparql = SPARQLWrapper(endpoint_url)

    # Set the SPARQL query
    query = """
    PREFIX helper: <http://www.ontotext.com/helper/>
    SELECT ?rdfSer WHERE {
    {
    	    SELECT (helper:rdf(helper:tuple(?s, ?p, ?o)) AS ?rdf) WHERE {
        	    ?s ?p ?o.
		    }
        }
        BIND(helper:serializeRDF(?rdf, "application/x-turtle") as ?rdfSer)
    }"""
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.queryAndConvert()
    return results["results"]["bindings"][0]["rdfSer"]["value"]

def query_gpt_assistant(query, context):
    stream = client.beta.threads.create_and_run(
    assistant_id="asst_BDUsPghZi3KbdfRDOGrvgTD4",
    thread={
        "messages": [
        {"role": "user", "content": query},
        {"role": "user", "content": "The context you will ground your response on is: " + context},
        ]
    },
    stream=True,
    )
    for event in stream:
        if(event.event == "thread.message.completed"):
            print(event)
            content_list = event.data.content
            text_content_block = content_list[0]
            text_obj = text_content_block.text
            value = text_obj.value
            print(value)
    
    query_context = query + "The context you will ground your response on is: " + context
    encoding = tiktoken.get_encoding("o200k_base")
    encoding = tiktoken.encoding_for_model("gpt-4o")
    enc = encoding.encode(query_context)
    query_context_cost = len(enc) * 0.0000025
    print(query_context_cost)

    enc = encoding.encode(value)
    response_cost = len(enc) * 0.00001
    print(response_cost)

    total_cost = query_context_cost + response_cost
    print(total_cost)
    
    return value

def main():
    repository, query = read_file()
    context = query_GraphDB(repository)
    response = query_gpt_assistant(query, context)
    write_file(response)
    #print(results)

main()