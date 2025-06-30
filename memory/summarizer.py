import os
import json
from datetime import datetime
from collections import defaultdict
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, MatchValue
from dotenv import load_dotenv
import duckdb

load_dotenv()

# === Clients ===
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "semantic_logs")
retention_db = duckdb.connect("../data/retention_boosts.duckdb")

# === Ensure Table Exists ===
def init_retention_db():
    retention_db.execute("""
        CREATE TABLE IF NOT EXISTS memory_retention_boosts (
            log_id TEXT PRIMARY KEY,
            boost FLOAT
        )
    """)

# === Helper: Filter logs older than N days ===
def get_old_logs(days_old=30):
    results, _ = qdrant.scroll(collection_name=COLLECTION_NAME, limit=500)
    old_logs = []
    for item in results:
        ts_str = item.payload.get("timestamp")
        if not ts_str or item.payload.get("archived"):
            continue
        try:
            ts = datetime.fromisoformat(ts_str)
            if (datetime.now() - ts).days >= days_old:
                old_logs.append(item.payload)
        except:
            continue
    return old_logs

# === Group logs by project and month ===
def group_logs(logs):
    groups = defaultdict(list)
    for log in logs:
        ts = datetime.fromisoformat(log["timestamp"])
        month_key = f"{log['project']}::{ts.year}-{ts.month:02}"
        groups[month_key].append(log)
    return groups

# === Summarize a group using GPT ===
def summarize_logs(logs, project, month_key):
    text = "\n".join([f"- {log['content']}" for log in logs])
    prompt = f"Summarize the following logs for project '{project}' during {month_key} into key decisions, impactful data points, and action items:\n\n{text}"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a senior technical summarizer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# === Write back summary to Qdrant ===
def upload_summary_to_qdrant(summary_text, project, month_key):
    vector = embedding_model.encode(summary_text).tolist()
    summary_log = {
        "log_id": f"summary::{project}::{month_key}",
        "content": summary_text,
        "timestamp": datetime.now().isoformat(),
        "project": project,
        "user": "summarizer",
        "type": "summary",
        "source": "summarizer"
    }
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(id=summary_log["log_id"], vector=vector, payload=summary_log)]
    )
    print(f"Uploaded summary for {project} {month_key}")

# === Archive original logs ===
def archive_logs(logs):
    for log in logs:
        log_id = log["log_id"]
        qdrant.set_payload(
            collection_name=COLLECTION_NAME,
            payload={"archived": True},
            points=[log_id]
        )
    print(f"📦 Archived {len(logs)} original logs.")

# === Add reinforcement boost to helpful logs ===
def reinforce_logs(logs):
    for log in logs:
        log_id = log.get("log_id")
        if not log_id:
            continue
        retention_db.execute("""
            INSERT INTO memory_retention_boosts (log_id, boost)
            VALUES (?, 0.05)
            ON CONFLICT (log_id) DO UPDATE SET boost = memory_retention_boosts.boost + 0.05
        """, (log_id,))
    print(f"🔁 Boosted {len(logs)} logs in memory_retention_boosts")

# === Entry point ===
def run_summarizer():
    init_retention_db()
    old_logs = get_old_logs(days_old=30)
    grouped = group_logs(old_logs)
    for month_key, logs in grouped.items():
        project = logs[0]["project"]
        summary_text = summarize_logs(logs, project, month_key)
        upload_summary_to_qdrant(summary_text, project, month_key)
        archive_logs(logs)
        reinforce_logs(logs)

if __name__ == "__main__":
    run_summarizer()
