import csv
from openai import AzureOpenAI
from pydantic import BaseModel
from typing import Literal
from api_keys import azure_openai_endpoint, azure_openai_key, azure_gpt41
from prompts import llm_judge_prompt
import json
import os


def extract_times_costs(entries: list[dict], output_path: str):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "time", "cost"])

        for entry in entries:
            question = entry["question"]
            time = entry["time_elapsed"]
            cost = entry["total_cost"]
            writer.writerow([question, time, cost])
            print(f"{question[:80]}: {time} {cost}")

def main():
    input_path = "./results/generated_30_03_threat_dragon_owasp_run3.json" #here change
    basename = os.path.splitext(os.path.basename(input_path))[0]
    output_path = f"./results/times_costs/{basename}.csv"
    with open(input_path) as f:
        entries = json.load(f)

    extract_times_costs(entries, output_path)

if __name__ == "__main__":
    main()