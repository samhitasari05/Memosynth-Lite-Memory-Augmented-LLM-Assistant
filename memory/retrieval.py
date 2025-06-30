from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import duckdb
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json
import numpy as np
from datetime import datetime
from scipy.spatial.distance import cosine
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

load_dotenv()

# Load embedding model and clients
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
qdrant = QdrantClient(host="localhost", port=6333)
duckdb_conn = duckdb.connect("../data/timeline_logs.duckdb")
neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URL"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

# ---------------------- Memory Source Fetchers ----------------------

def get_semantic_logs(query, top_k=5):
    vector = embedding_model.encode(query).tolist()
    
    results = qdrant.search(
        collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
        query_vector=vector,
        limit=top_k,
        query_filter=Filter(
            must_not=[
                FieldCondition(key="archived", match=MatchValue(value=True))
            ]
        )
    )

    logs = []
    for r in results:
        log = r.payload
        log["score"] = r.score
        log["source"] = "Qdrant"
        logs.append(log)

    # Prioritize summaries over individual logs if they exist
    summaries = [log for log in logs if log.get("type") == "summary"]
    non_summaries = [log for log in logs if log.get("type") != "summary"]

    final_logs = summaries + non_summaries
    return final_logs[:top_k]


def get_timeline_logs(since="2024-03-01"):
    query = f"""
        SELECT * FROM timeline_logs
        WHERE timestamp > '{since}'
        ORDER BY timestamp DESC
        LIMIT 5
    """
    results = duckdb_conn.execute(query).fetchdf()
    logs = results.to_dict("records")
    for log in logs:
        log["source"] = "DuckDB"
    return logs

def get_relational_logs(project=None, session_id=None):
    with neo4j_driver.session() as session:
        if project:
            result = session.run(
                "MATCH (l:Log)-[:RELATED_TO]->(:Project {name: $project}) RETURN l LIMIT 5",
                project=project
            )
            logs = [r["l"] for r in result]
        elif session_id:
            result = session.run(
                "MATCH (l:Log {session_id: $sid})-[:RELATED_TO*1..2]-(n:Log) RETURN n LIMIT 5",
                sid=session_id
            )
            logs = [r["n"] for r in result]
        else:
            return []

        for log in logs:
            log["source"] = "Neo4j"
        return logs

# ---------------------- CRAG-Style Multi-Head Relevance ----------------------

def compute_crag_score(log, query_vector, query_project=None):
    # Semantic similarity
    log_vector = embedding_model.encode(log.get("content", "")).tolist()
    semantic_sim = 1 - cosine(query_vector, log_vector)

    # Recency score
    try:
        ts = datetime.fromisoformat(log["timestamp"])
        age_days = (datetime.now() - ts).days
        recency = np.exp(-age_days / 30)
    except:
        recency = 0.5

    # Project match
    project_match = 1.0 if log.get("project") == query_project else 0.0

    # Speaker priority
    speaker = log.get("user", "").lower()
    speaker_weights = {"carol": 1.0, "eve": 0.7, "bob": 0.5}
    speaker_score = speaker_weights.get(speaker, 0.2)

    # Retention boost (from DuckDB)
    boost = 0.0
    try:
        query = f"SELECT boost FROM memory_retention_boosts WHERE log_id = '{log['log_id']}'"
        result = duckdb_conn.execute(query).fetchone()
        if result:
            boost = float(result[0])
    except:
        boost = 0.0

    # Final weighted score
    total_score = (
        0.4 * semantic_sim +
        0.3 * recency +
        0.2 * project_match +
        0.1 * speaker_score +
        boost  # additive bonus
    )

    log["score"] = total_score
    return total_score

# ---------------------- Combiner with Adaptive Forgetting + Score Filtering ----------------------

RELEVANCE_THRESHOLD = 0.4  

def get_combined_logs(query, since="2024-03-01", top_k=12, return_discarded=False):
    semantic = get_semantic_logs(query)
    timeline = get_timeline_logs(since)
    related = get_relational_logs(project=semantic[0]["project"] if semantic else None)

    all_logs = semantic + timeline + related
    seen_ids = set()
    combined = []

    query_vector = embedding_model.encode(query)
    query_project = semantic[0].get("project") if semantic else None

    for log in all_logs:
        log_id = log.get("log_id")
        if log_id and log_id not in seen_ids:
            score = compute_crag_score(log, query_vector, query_project)
            log["score"] = round(score, 4)
            combined.append(log)
            seen_ids.add(log_id)

    combined.sort(key=lambda x: x["score"], reverse=True)

    retained = [log for log in combined if log["score"] >= RELEVANCE_THRESHOLD][:top_k]
    discarded = [log for log in combined if log["score"] < RELEVANCE_THRESHOLD]

    if return_discarded:
        return retained, discarded
    else:
        return retained
