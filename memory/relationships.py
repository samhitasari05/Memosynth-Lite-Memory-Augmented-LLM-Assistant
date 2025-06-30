from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Neo4j connection
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URL"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)

# Load logs
LOG_FILE = "../data/filtered_memory_logs.jsonl"

def add_project_relationships(tx, log):
    tx.run("""
        MERGE (p:Project {name: $project})
        WITH p
        MATCH (l:Log {log_id: $log_id})
        MERGE (l)-[:RELATED_TO]->(p)
    """, project=log["project"], log_id=log["log_id"])


def main():
    with driver.session() as session:
        with open(LOG_FILE, "r") as f:
            for line in f:
                log = json.loads(line)
                session.write_transaction(add_project_relationships, log)
    
    print("Project relationships added to Neo4j.")

if __name__ == "__main__":
    main()
