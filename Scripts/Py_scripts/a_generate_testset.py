from api_keys import azure_openai_endpoint, azure_openai_key, azure_gpt41
from a_textual_descriptions import text_description_owasp
from prompts import ground_truths_generation_prompt
from openai import AzureOpenAI
from questions import questions_list_owasp
import json

client = AzureOpenAI(api_key=azure_openai_key, azure_endpoint=azure_openai_endpoint, api_version="2025-01-01-preview")

text_desc = f"""\n The text descriptions you will ground your response on are: {text_description_owasp}"""

def generate_answer_question(question: str):
    response = client.chat.completions.create(
        model=azure_gpt41,
        temperature=0,
        seed=123,
        messages=[
            {"role": "system", "content": ground_truths_generation_prompt},
            {"role": "system", "content": text_desc},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

def write_to_json(filepath: str, data: list[dict]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    file_particle = "./testsets"
    testset = []
    for question in questions_list_owasp:
        question_response = generate_answer_question(question["question"])
        testset.append({"category_id": question["category_id"], "question_id": question["question_id"], "question": question["question"], "ground_truth": question_response})
    
    filepath = file_particle+"/generated_28_03_owasp_v1.json"
    write_to_json(filepath, testset)

if __name__ == "__main__":
    main()