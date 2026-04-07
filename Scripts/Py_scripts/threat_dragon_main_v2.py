from threat_dragon_parser_simple import ThreatDragonIndex
from openai import AzureOpenAI
from prompts import (
    question_decomposition_prompt_v2,
    entities_of_interest_extraction_prompt_v2,
    llm_answer_generation_prompt,
    transform_context_natural_language_owasp_prompt,
    threat_dragon_function_selection_prompt
)
from api_keys import azure_openai_endpoint, azure_openai_key, azure_gpt41
import json
from cost_tracker import CostTracker
import time
from questions import questions_truths_list_owasp
from pydantic import BaseModel
from typing import Literal

client = AzureOpenAI(
    api_key=azure_openai_key,
    azure_endpoint=azure_openai_endpoint,
    api_version="2025-01-01-preview",
)

idx = ThreatDragonIndex()
idx.load("./owasp_models/Case2_Patient_Admission.json")
idx.load("./owasp_models/Case2_Pharmacy.json")  # fallback

class IntentsCollection(BaseModel):
    intents: list[str]

class EntitiesOfInterestCollection(BaseModel):
    entities_of_interest: list[str]

class RetrievalFunctionClass(BaseModel):
    retrieval_function: Literal["get_threats_for", "get_mitigations_for", "get_connected_flows", "get_trust_boundary_for", "search", "extract_context"]

def write_to_json(filepath: str, data: list[dict]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def split_user_question_intents(question: str, tracker: CostTracker, max_retries=2):
    for attempt in range(max_retries + 1):
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
    print(f"FAILED all retries for split_user_question_intents: {question[:80]}")
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
                {"role": "user", "content": question},
            ],
        )
        tracker.track(response.usage, "respond_to_question")
        return response.choices[0].message.content
    except Exception as e:
        print(f"ERROR in respond_to_question: {e}")
        return ""

def choose_retrieval_function(question: str, tracker: CostTracker, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            response = client.beta.chat.completions.parse(
                model=azure_gpt41,
                temperature=0,
                seed=123,
                max_tokens=200,
                response_format=RetrievalFunctionClass,
                messages=[
                    {"role": "system", "content": threat_dragon_function_selection_prompt},
                    {"role": "user", "content": question},
                ],
            )
            if response.choices[0].finish_reason == "length":
                print(f"WARNING: Truncated in split_intents for: {question[:80]}")
                return []
            tracker.track(response.usage, "split_intents")
            return response.choices[0].message.parsed.retrieval_function
        except Exception as e:
            print(f"ERROR in split_user_question_intents: {e}")
    print(f"FAILED all retries for split_user_question_intents: {question[:80]}")
    return "extract_context"

def extract_context_for_question(entity_of_interest: str):
    context = idx.extract_context(entity_of_interest)
    
    return context

def transform_context_natural_language(context: str):
    try:
        context_str = str(context)
        response = client.chat.completions.create(
            model=azure_gpt41,
            temperature=0,
            seed=123,
            messages=[
                {"role": "system", "content": transform_context_natural_language_owasp_prompt},
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
    questions_ground_truths_owasp = []

    for question in questions_truths_list_owasp:
        print(f"""Processing question: {question["question_id"]} {question["question"]}""")
        try:
            question_context = ""
            tracker = CostTracker(input_price_per_1k=0.002, output_price_per_1k=0.008)
            start = time.time()

            intents = split_user_question_intents(question["question"], tracker)
            for intent in intents:
                entities_of_interest = extract_entities_of_interest(intent, tracker)
                for entity in entities_of_interest:
                    #retrieval_function = choose_retrieval_function(intent, tracker)
                    #print(retrieval_function)
                    context = extract_context_for_question(entity)
                    question_context = question_context + str(context)
            
            response = respond_to_question(question["question"], question_context, tracker)
            end = time.time()
            total_time = end - start

            natural_language_context = transform_context_natural_language(question_context)

            record = {
                "category_id": question["category_id"],
                "question_id": question["question_id"],
                "question": question["question"],
                "response": response,
                "ground_truth": question["ground_truth"],
                "context_json": question_context,
                "context_natural_language": natural_language_context,
                "time_elapsed": total_time,
                "total_cost": tracker.total_cost,
            }

            questions_ground_truths_owasp.append(record)

        except Exception as e:
            print(f"FAILED on question {question['question_id']}: {e}")
            questions_ground_truths_owasp.append(
                {
                    "category_id": question["category_id"],
                    "question_id": question["question_id"],
                    "question": question["question"],
                    "error": str(e),
                }
            )
            continue

    file_name = "generated_30_03_threat_dragon_owasp_run3.json"
    file_particle = "./results"
    filepath = file_particle + f"/{file_name}"
    write_to_json(filepath, questions_ground_truths_owasp)


if __name__ == "__main__":
    main()