import json
from api_keys import azure_gpt41, azure_openai_endpoint, azure_openai_key
from prompts import transform_context_natural_language_prompt
from openai import AzureOpenAI
from ontology import ontology

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


OUTPUT_FILE = "./results/new_gen.json"

with open("./results/kg_context_generated_30_03_2_hops_owasp_run4.json") as f: #here modify context graph
    d = json.load(f)

with open("./results/generated_30_03_2_hops_owasp_run4.json") as file: #here modify data file
    data = json.load(file)

# Load existing progress if the output file already exists
try:
    with open(OUTPUT_FILE) as f:
        data = json.load(f)
    print(f"Resumed from existing output file with {len(data)} entries.")
except (FileNotFoundError, json.JSONDecodeError):
    print("Starting fresh.")

for i in range(21):
    # Skip if already processed
    if data[i].get("context_natural_language"):
        print(f"Skipping already processed question: {data[i]['question_id']} {data[i]['question']}")
        continue

    print(f"Processing question: {data[i]['question_id']} {data[i]['question']}")
    natural_language_context = transform_context_natural_language(d[i])
    data[i]["context_natural_language"] = natural_language_context

    # Write after each question to prevent data loss
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"  Saved progress ({i + 1}/21)")

print("Done.")