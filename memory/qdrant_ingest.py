import json
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from sentence_transformers import SentenceTransformer
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# ---- Config ----
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION_NAME")
EMBED_MODEL = "all-MiniLM-L6-v2"
DATA_FILE = "../data/memory_logs_with_historic_impact.jsonl"

# ---- Init clients ----
qdrant = QdrantClient(host="localhost", port=6333)
model = SentenceTransformer(EMBED_MODEL)

# ---- Load logs ----
logs = []
with open(DATA_FILE, "r") as f:
    for line in f:
        log = json.loads(line)
        if "log_id" not in log:
            log["log_id"] = str(uuid.uuid4())
        log["archived"] = False  # for adaptive forgetting
        logs.append(log)

# ---- Embed and write to Qdrant ----
points = []
for log in logs:
    embedding = model.encode(log["content"]).tolist()
    point = PointStruct(
        id=log["log_id"],
        vector=embedding,
        payload=log
    )
    points.append(point)

print(f"Ingesting {len(points)} logs into Qdrant collection: {QDRANT_COLLECTION}")
qdrant.upsert(
    collection_name=QDRANT_COLLECTION,
    points=points
)
print("Ingestion complete.")
