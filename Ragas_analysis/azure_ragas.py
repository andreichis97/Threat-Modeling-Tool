import os
from api_keys import azure_openai_endpoint, azure_openai_key
from langchain_openai.chat_models import AzureChatOpenAI
from langchain_openai.embeddings import AzureOpenAIEmbeddings
from ragas import evaluate
from ragas.metrics import _context_precision, _context_recall, _answer_relevancy, _faithfulness
from ragas.run_config import RunConfig
from datasets import Dataset
import json

analysis_metrics = [
    _faithfulness,
    _answer_relevancy,
    _context_recall,
    _context_precision
]

os.environ["AZURE_OPENAI_API_KEY"] = azure_openai_key
azure_configs = {
    "base_url": azure_openai_endpoint,
    "model_deployment": "gpt-4o-ragas",
    "model_name": "gpt-4o",
    "embedding_deployment": "text-embedding-ada-002",
    "embedding_name": "text-embedding-ada-002",  # most likely
}

run_config = RunConfig(
    timeout=120,
    max_retries=15,
    max_wait=90,
    max_workers=16
)

azure_model = AzureChatOpenAI(
    openai_api_version="2025-01-01-preview",
    azure_endpoint=azure_configs["base_url"],
    azure_deployment=azure_configs["model_deployment"],
    model=azure_configs["model_name"],
    validate_base_url=False,
)

azure_embeddings = AzureOpenAIEmbeddings(
    openai_api_version="2025-01-01-preview",
    azure_endpoint=azure_configs["base_url"],
    azure_deployment=azure_configs["embedding_deployment"],
    model=azure_configs["embedding_name"],
)

input_path = "./datasets/generated_30_03_2_hops_owasp_run3.json" #here change
basename = os.path.splitext(os.path.basename(input_path))[0]
output_path = f"./results/{basename}.csv"

with open(input_path) as f:
    d = json.load(f)

questions = []
ground_truths = []
answers = []
contexts = []

for entry in d:
    questions.append(entry["question"])
    ground_truths.append(entry["ground_truth"])
    answers.append(entry["response"])
    
    if isinstance(entry["context_natural_language"], str):
        context = [entry["context_natural_language"]]
        contexts.append(context)
    elif isinstance(entry["context_natural_language"], list):
        #contexts.append(entry["context_natural_language"])
        contexts.append(["\n\n".join(entry["context_natural_language"])])

data = {
    "question": questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truths": ground_truths,
    "reference": ground_truths   
}

dataset = Dataset.from_dict(data)
result = evaluate(
    dataset = dataset,
    metrics = analysis_metrics,
    llm = azure_model,
    embeddings = azure_embeddings,
    run_config = run_config
)

df = result.to_pandas()
df = df[["user_input", "faithfulness", "answer_relevancy", "context_recall", "context_precision"]]
df.to_csv(output_path, index=False, encoding="utf8")