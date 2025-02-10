from api_keys import openai_api_key
import os
from SPARQLWrapper import SPARQLWrapper, JSON, N3
from openai import OpenAI
import tiktoken
import ollama

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

def identify_query_subject(user_query):
    prefilled_prompt_sys_claude = """
    You are an advanced language analysis assistant specializing in subject identification within sentences or phrases. Your task is to accurately identify and categorize the subject in any given text.
    Instructions:
    1. Carefully read and analyze the input text.
    2. Identify all potential subjects in the text. Subjects can include, but are not limited to:
    - Data Flow Diagrams
    - Threat Modeling Diagrams
    - Data Stores
    - Data Flows
    - External Entities
    - Processes
    - Business Processes
    - Systems (political systems, ecosystems, technological systems)

    3. Consider the context of the text to ensure accurate subject identification, especially in cases of ambiguity or multiple interpretations.

    4. Categorize each identified subject based on the most appropriate category from the list above or a relevant subcategory.
    5. When providing the response, write just the identified subject, as it is written in text, without any additional information.
    6. Examples:
        If the given text is: Give me information about OrderManager, the subject is OrderManager
        If the given text is: What is Appropriate authentication?, the subject is Appropriate authentication
        If the given text is: Find all the threats of ProductDataStore, the subject is ProductDataStore
    """
    user_prompt = "Identify the subject in: " + user_query

    response = ollama.chat(model="llama3.1", options={"temperature":0}, 
            messages = [
                {"role": "system", "content": prefilled_prompt_sys_claude},
                {"role": "user", "content": user_prompt}
            ],           
        )
    return response["message"]["content"]

def get_labels(repository):
    labels = []
    endpoint_url = f"""http://localhost:7200/repositories/{repository}"""
    sparql = SPARQLWrapper(endpoint_url)
    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?label
    WHERE
    {
        ?sub rdfs:label ?label
    }"""
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.queryAndConvert()

    res = results["results"]["bindings"]
    for r in res:
        label = r["label"]["value"]
        labels.append(label)

    return labels

def process_query_subject(subject, labels):
    prefilled_prompt_sys_claude = """
    You are an advanced language analysis assistant specializing in words normalization. Your task is to accurately identify if a word or suite of words exist or not in a given list. If they exist pick the word / phrase as they are written. If they don't exist pick the closest matching entry from the given list.
    Instructions:
    1. Carefully read the given word or sequence of words.
    2. Carefully read the list of words / word sequences
    3. If the word or word sequence exists as is in the sentence, return the given word or word sequence. If not, return the closest matchig entry from the list. Always respond without any additional information or comments.
    4. Examples:
        If the given word or sequence of words is: Order Manager and the list contains ['OrderManager', 'Don't store secrets', 'ProcLog'] the response is OrderManager
        If the given word or sequence of words is: ProzcLogz and the list contains ['OrderManager', 'Don't store secrets', 'ProcLog'] the response is ProcLog
        If the given word or sequence of words is: Don't store secrets and the list contains ['OrderManager', 'Don't store secrets', 'ProcLog'] the response is Don't store secrets
    """
    user_prompt = "The given word or word sequence is: " + subject + "and the list to compare with is: " + labels

    response = ollama.chat(model="llama3.1", options={"temperature":0}, 
            messages = [
                {"role": "system", "content": prefilled_prompt_sys_claude},
                {"role": "user", "content": user_prompt}
            ],           
        )
    return response["message"]["content"]

def query_GraphDB(repository, subject):

    #repository = "threat_modeling"
    # Set the endpoint URL of the graph database server
    endpoint_url = f"""http://localhost:7200/repositories/{repository}"""

    # Create a new SPARQLWrapper instance
    sparql = SPARQLWrapper(endpoint_url)

    # Set the SPARQL query
    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX : <http://www.example.org#>
    CONSTRUCT 
    {
        ?lookingFor ?relation1 ?ob.
        ?ob ?relation2 ?otherOb.
        ?otherOb ?relation3 ?ob.
        ?ob ?relation4 ?lookingFor.
        ?otherOb ?relation5 ?otherOtherOb.
        ?previousOb ?relation6 ?otherOb.
    }
    WHERE
    {
        {
            ?lookingFor rdfs:label """ + "'" + subject + "'" + """; 
                ?relation1 ?ob. 
            ?ob ?relation2 ?otherOb.
        }
        UNION
        {
            ?lookingFor rdfs:label """ + "'" + subject + "'" + """; 
                ?relation1 ?ob. 
            ?ob ?relation2 ?otherOb.
            ?otherOb ?relation5 ?otherOtherOb.
        }
        UNION
        {
            ?otherOb ?relation3 ?ob. 
            ?ob ?relation4 ?lookingFor.
            ?lookingFor rdfs:label """ + "'" + subject + "'" + """. 
        }
        UNION
        {
            ?previousOb ?relation6 ?otherOb.
            ?otherOb ?relation3 ?ob. 
            ?ob ?relation4 ?lookingFor.
            ?lookingFor rdfs:label """ + "'" + subject + "'" + """. 
        }
    }"""
    sparql.setQuery(query)
    sparql.setReturnFormat(N3)
    results = sparql.queryAndConvert().decode("utf-8")
    return results
    #return results["results"]["bindings"][0]["rdfSer"]["value"]

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
    subject = identify_query_subject(query)
    print(subject)

    labels = get_labels(repository)
    print(labels)

    final_subject = process_query_subject(subject, str(labels))
    print(final_subject)
    
    context = query_GraphDB(repository, final_subject)
    response = query_gpt_assistant(query, context)
    write_file(response)
    #print(results)

main()