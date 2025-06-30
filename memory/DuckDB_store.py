import duckdb
import json
from pathlib import Path

# Input and Output Paths
#INPUT_FILE = "../data/filtered_memory_logs.jsonl"
INPUT_FILE = "../data/memory_logs_with_historic_impact.jsonl"
DUCKDB_PATH = "timeline_logs.duckdb"

# Create database and table if not exist
def init_duckdb():
    conn = duckdb.connect(DUCKDB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS timeline_logs (
            log_id TEXT,
            timestamp TIMESTAMP,
            user TEXT,
            project TEXT,
            type TEXT,
            content TEXT,
            session_id TEXT
        )
    """)
    conn.close()

# Load logs from JSONL and insert into DuckDB
def load_logs_to_duckdb():
    conn = duckdb.connect(DUCKDB_PATH)

    with open(INPUT_FILE, "r") as f:
        for line in f:
            log = json.loads(line)
            conn.execute("""
                INSERT INTO timeline_logs VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                log["log_id"],
                log["timestamp"],
                log["user"],
                log["project"],
                log["type"],
                log["content"],
                log["session_id"]
            ))
    conn.close()
    print(f"Inserted logs into DuckDB at: {DUCKDB_PATH}")

# Run
if __name__ == "__main__":
    init_duckdb()
    load_logs_to_duckdb()

def preview_duckdb_logs(n=5):
    conn = duckdb.connect(DUCKDB_PATH)
    df = conn.execute(f"SELECT * FROM timeline_logs LIMIT {n}").fetchdf()
    print(df)

if __name__ == "__main__":
    init_duckdb()
    load_logs_to_duckdb()
    preview_duckdb_logs() 
