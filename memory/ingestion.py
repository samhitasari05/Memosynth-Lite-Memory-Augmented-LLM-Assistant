# core/ingestion.py

import json
import os
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm

# File paths
INPUT_FILE = "../data/memory_logs_with_duplicates.jsonl"
OUTPUT_FILE = "data/filtered_memory_logs.jsonl"

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

def load_logs(path):
    with open(path, "r") as f:
        return [json.loads(line) for line in f]

def save_logs(path, logs):
    with open(path, "w") as f:
        for log in logs:
            f.write(json.dumps(log) + "\n")

def deduplicate_logs(logs, similarity_threshold=0.9):
    unique_logs = []
    seen_embeddings = []

    for log in tqdm(logs, desc="Filtering logs"):
        content = log["content"]
        embedding = model.encode(content, convert_to_tensor=True)

        is_duplicate = False
        for existing in seen_embeddings:
            sim_score = util.pytorch_cos_sim(embedding, existing).item()
            if sim_score > similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            seen_embeddings.append(embedding)
            unique_logs.append(log)

    return unique_logs

if __name__ == "__main__":
    logs = load_logs(INPUT_FILE)
    print(f"🔍 Loaded {len(logs)} logs with possible duplicates.")

    filtered = deduplicate_logs(logs)
    print(f"Deduplicated logs: {len(filtered)} remaining.")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    save_logs(OUTPUT_FILE, filtered)
    print(f"Saved to {OUTPUT_FILE}")
