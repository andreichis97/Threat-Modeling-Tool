import json
from api_keys import azure_gpt41, azure_openai_endpoint, azure_openai_key
from prompts import transform_context_natural_language_prompt
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=azure_openai_key,
    azure_endpoint=azure_openai_endpoint,
    api_version="2025-01-01-preview",
)

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


with open("./results/kg_context_generated_19_03_3_hops_run2.json") as f:
    d = json.load(f)

with open("./results/generated_19_03_3_hops_run2.json") as file:
    data = json.load(file)

for i in range(55):
    print(f"Processing question: {data[i]["question_id"]} {data[i]["question"]}")
    natural_language_context = transform_context_natural_language(d[i])
    data[i]["context_natural_language"] = natural_language_context

with open("./results/new_gen.json", "w") as f:
    json.dump(data, f, indent=2)