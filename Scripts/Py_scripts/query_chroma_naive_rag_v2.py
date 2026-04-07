from openai import AzureOpenAI
from prompts import (
    question_decomposition_prompt_v2,
    llm_answer_generation_prompt_chroma,
)
from api_keys import azure_openai_endpoint, azure_openai_key, azure_gpt41
from pydantic import BaseModel
import time
from questions import questions_truths_list
from cost_tracker import CostTracker
import json
import chromadb

chroma_client = chromadb.PersistentClient(path="./persistent_embeddings_chroma")
chroma_client.heartbeat()

EMBEDDING_MODEL = "text-embedding-3-large"

client = AzureOpenAI(
    api_key=azure_openai_key,
    azure_endpoint=azure_openai_endpoint,
    api_version="2025-01-01-preview",
)


class IntentsCollection(BaseModel):
    intents: list[str]


def write_to_json(filepath: str, data: list[dict]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def query_chromadb(
    question: str,
    tracker: CostTracker,
    collection_name: str = "shopnova_threat_model",
    n_results: int = 5,
) -> list[str]:
    """Query ChromaDB with a natural language question."""
    collection = chroma_client.get_collection(name=collection_name)

    response = client.embeddings.create(input=[question], model=EMBEDDING_MODEL)
    tracker.track(response.usage, "embedding")
    query_embedding = response.data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    # results["documents"] is [[doc1, doc2, ...]] — return the inner list
    return results["documents"][0]


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
            print(f"WARNING: Truncated in split_intents for: {question[:80]}")
            return []
        tracker.track(response.usage, "split_intents")
        return response.choices[0].message.parsed.intents
    except Exception as e:
        print(f"ERROR in split_user_question_intents: {e}")
        return []


def extract_context_for_question(
    question: str, tracker: CostTracker
) -> list[str]:
    intents = split_user_question_intents(question, tracker)
    if not intents:
        print("WARNING: No intents extracted, using original question as single intent")
        intents = [question]

    flat_contexts = []
    for intent in intents:
        docs = query_chromadb(intent, tracker, n_results=5)
        #print(docs)
        flat_contexts.extend(docs)

    return flat_contexts


def respond_to_question(
    question: str, context: list[str], tracker: CostTracker
) -> str:
    try:
        context_str = "\n\n---\n\n".join(context)
        response = client.chat.completions.create(
            model=azure_gpt41,
            temperature=0,
            seed=123,
            messages=[
                {"role": "system", "content": llm_answer_generation_prompt_chroma},
                {
                    "role": "system",
                    "content": "The context you will rely on is:\n\n" + context_str,
                },
                {"role": "user", "content": question},
            ],
        )
        tracker.track(response.usage, "respond_to_question")
        return response.choices[0].message.content
    except Exception as e:
        print(f"ERROR in respond_to_question: {e}")
        return ""


def main():
    questions_ground_truths = []

    for question in questions_truths_list:
        print(
            f"""Processing question: {question["question_id"]} {question["question"]}"""
        )
        try:
            tracker = CostTracker(input_price_per_1k=0.002, output_price_per_1k=0.008)
            start = time.time()

            context_for_question = extract_context_for_question(
                question["question"], tracker
            )
            response = respond_to_question(
                question["question"], context_for_question, tracker
            )

            end = time.time()
            total_time = end - start

            record = {
                "category_id": question["category_id"],
                "question_id": question["question_id"],
                "question": question["question"],
                "response": response,
                "ground_truth": question["ground_truth"],
                "context_natural_language": context_for_question,
                "time_elapsed": total_time,
                "total_cost": tracker.total_cost,
            }

            questions_ground_truths.append(record)

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

    file_name = "generated_20_03_naive_rag_run3.json"
    filepath = f"./results/{file_name}"
    write_to_json(filepath, questions_ground_truths)

if __name__ == "__main__":
    main()