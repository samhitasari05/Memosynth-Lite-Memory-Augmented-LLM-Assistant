import os
import json
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer

# Load env vars
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "semantic_logs"

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
model = SentenceTransformer("all-MiniLM-L6-v2")

# Create collection if not exists
def init_qdrant():
    if COLLECTION_NAME not in client.get_collections().collections:
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

# Upload filtered logs
def upload_to_qdrant(path):
    with open(path, "r") as f:
        logs = [json.loads(line) for line in f]

    points = []
    for log in logs:
        embedding = model.encode(log["content"]).tolist()
        points.append(PointStruct(id=log["log_id"], vector=embedding, payload=log))

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Uploaded {len(points)} logs to Qdrant collection: {COLLECTION_NAME}")

if __name__ == "__main__":
    init_qdrant()
    upload_to_qdrant("../data/filtered_memory_logs.jsonl")
