import os
import json
from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Load environment variables
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Path to filtered logs
#LOG_FILE = "../data/filtered_memory_logs.jsonl"
LOG_FILE = "../data/memory_logs_with_historic_impact.jsonl"


# Connect to Neo4j
driver = GraphDatabase.driver(
os.getenv("NEO4J_URL"),
auth=basic_auth(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

def load_logs(path):
    with open(path, "r") as f:
        return [json.loads(line) for line in f]


def insert_log(tx, log):
    tx.run("""
        MERGE (u:User {name: $user})
        MERGE (p:Project {name: $project})
        MERGE (s:Session {id: $session_id})
        MERGE (t:Type {name: $type})
        CREATE (l:Log {
            id: $log_id,
            timestamp: datetime($timestamp),
            content: $content
        })
        MERGE (u)-[:CREATED]->(l)
        MERGE (l)-[:BELONGS_TO]->(p)
        MERGE (l)-[:IN_SESSION]->(s)
        MERGE (l)-[:IS_TYPE]->(t)
    """, log)


def init_neo4j():
    logs = load_logs(LOG_FILE)
    with driver.session() as session:
        for log in logs:
            session.write_transaction(insert_log, log)
    print(f"Inserted {len(logs)} logs into Neo4j.")


if __name__ == "__main__":
    init_neo4j()
