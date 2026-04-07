import csv
from openai import AzureOpenAI
from pydantic import BaseModel
from typing import Literal
from api_keys import azure_openai_endpoint, azure_openai_key, azure_gpt41
from prompts import llm_judge_prompt
import json
import os

client = AzureOpenAI(
    api_key=azure_openai_key,
    azure_endpoint=azure_openai_endpoint,
    api_version="2025-01-01-preview",
)

class JudgeVerdict(BaseModel):
    verdict: Literal["correct", "partially_correct", "incorrect"]


def judge_and_write(entries: list[dict], output_path: str):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "verdict"])

        for entry in entries:
            question = entry["question"]
            response = entry["response"]
            ground_truth = entry["ground_truth"]

            user_message = f"Question: {question}\nResponse: {response}\nGround Truth: {ground_truth}"

            verdict = "error"
            for attempt in range(3):
                try:
                    result = client.beta.chat.completions.parse(
                        model=azure_gpt41,
                        temperature=0,
                        seed=123,
                        response_format=JudgeVerdict,
                        messages=[
                            {"role": "system", "content": llm_judge_prompt},
                            {"role": "user", "content": user_message},
                        ],
                    )
                    verdict = result.choices[0].message.parsed.verdict
                    break
                except Exception as e:
                    print(f"Attempt {attempt + 1}/3 failed for: {question[:80]} — {e}")

            writer.writerow([question, verdict])
            print(f"{verdict}: {question[:80]}")

def main():
    input_path = "./results/generated_30_03_threat_dragon_owasp_run3.json" #here change
    basename = os.path.splitext(os.path.basename(input_path))[0]
    output_path = f"./results/judged_responses/{basename}.csv"
    with open(input_path) as f:
        entries = json.load(f)

    judge_and_write(entries, output_path)

if __name__ == "__main__":
    main()