## MemoSynth-Lite: Memory-Augmented LLM Assistant

MemoSynth-Lite is a lightweight, privacy-conscious memory system that augments LLMs with structured long-term memory using Qdrant, DuckDB, and Neo4j. It simulates how agents can remember past conversations, summarize insights, and deliver context-rich responses — all stored and retrieved across semantic, temporal, and relational memory layers.

---

## Features

- Vector-based semantic memory (Qdrant)
- Timeline-based memory logs (DuckDB)
- Graph-based relationship tracking (Neo4j)
- Memory deduplication, scoring, and forgetting
- Streamlit UI to compare LLM vs LLM+Memory
- Full local execution, no external API sharing
- Privacy-aware design with deletion, TTL, and anonymization

---

## Architecture
```
+--------------------------------------------------+
| Synthetic Log Generator                          |
| (memory_logs_with_historic_impact.jsonl)         |
| Techniques:                                      |
| - Faker-generated data with timestamps           |
| - Multiple memory types (decision, summary, etc) |
| - Controlled duplicates (~10%)                   |
| - Historic impact logs (>30 days)                |
+--------------------------------------------------+
                            |
                            v
+--------------------------------------------------+
| Log Ingestion Phase                              |
| Scripts:                                         |
| - qdrant_ingest.py                               |
| - duckdb_store.py                                |
| - neo4j_store.py                                 |
| Techniques:                                      |
| - ID-preserving bulk insert                      |
| - Reproducible metadata schema                   |
| - Local file-based ingestion                     |
+--------------------------------------------------+
         |                         |                          |
         v                         v                          v
+----------------------------+ +--------------------------+ +-----------------------------+
| Qdrant: Semantic Vector DB | | DuckDB: Timeline Storage| | Neo4j: Graph Memory Store   |
|                            | |                          | |                             |
| Techniques:                | | Techniques:              | | Techniques:                 |
| - SentenceTransformer      | | - SQL schema for logs    | | - Entity-Relation graph     |
|   ("all-MiniLM-L6-v2")     | | - ORDER BY timestamp     | | - Nodes: User, Project,     |
| - Payloads store full log  | | - Filtering by date      | |   Type, Session             |
| - Upsert with UUIDs        | |                          | | - Relationships: CREATED,   |
|                            | |                          | |   BELONGS_TO, IS_TYPE, etc. |
+----------------------------+ +--------------------------+ +-----------------------------+
          \                        |                             /
           \                       |                            /
            \                      |                           /
             v                     v                          v
+-------------------------------------------------------------------------------+
| Background Log Processing & Memory Logic                                     |
| - Summarization (for logs older than 30 days)                                |
|   Techniques:                                                                |
|   - Group logs by Project + Month                                            |
|   - Extract impactful metrics from content (e.g. revenue figures)            |
|   - Use GPT-4o for summarization with compression                            |
|   - Store as new memory with "type": "summary"                               |
|                                                                               |
| - Adaptive Forgetting                                                        |
|   Techniques:                                                                |
|   - Filter out old logs after summary creation                               |
|   - TTL-based logic or relevance thresholding (optional)                     |
|   - Archive (local JSONL) but not delete from disk                           |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+--------------------------------------------------------------------------------------+
| Memory Retrieval + Fusion Engine (generate_response.py)                             |
|                                                                                      |
| Techniques:                                                                          |
| - Query input converted into vector (MiniLM)                                         |
| - Search top-k from Qdrant (semantic)                                                |
| - Pull relevant logs from DuckDB (recency-aware)                                     |
| - Pull connected logs from Neo4j (relational memory)                                 |
| - Apply CRAG scoring:                                                                |
|     - Cosine similarity                                                              |
|     - Recency boost                                                                  |
|     - Association strength from Neo4j                                                |
| - Tag each memory with source ("Qdrant", "Neo4j", etc.)                              |
| - Filter out logs below relevance threshold (discarded logs visible in UI)          |
+--------------------------------------------------------------------------------------+
                                        |
                                        v
+--------------------------------------------------------------------------------------+
| LLM Grounded Answer Generation                                                       |
|                                                                                      |
| Techniques:                                                                          |
| - Construct final augmented prompt:                                                  |
|   "Given these logs: [...], answer: [question]"                                      |
| - Query OpenAI GPT-4o (or fallback model)                                            |
| - Display both:                                                                      |
|   - Memory-grounded answer                                                           |
|   - LLM-alone answer                                                                 |
| - Store generated answer as a memory log (optional extension)                        |
+--------------------------------------------------------------------------------------+
                                        |
                                        v
+--------------------------------------------------------------------------------------+
| Streamlit UI (app.py)                                                                |
|                                                                                      |
| Features:                                                                            |
| - Input field: Ask any question                                                      |
| - Output pane:                                                                       |
|     - Qdrant/DuckDB/Neo4j retrieved logs (colored tags, collapsible)                |
|     - Generated Answer vs. Raw LLM Answer                                            |
|     - Plotly bar chart of relevance scores                                           |
|     - Discarded logs shown in collapsible section                                    |
|     - Summary logs collapsed by default                                              |
|                                                                                      |
| - Optional Input Filters:                                                            |
|     - By Project                                                                     |
|     - By Memory Type                                                                 |
|                                                                                      |
| - Advanced:                                                                          |
|     - Log source tracking                                                            |
|     - Future: User tagging / "forget this" interaction                               |
+--------------------------------------------------------------------------------------+
                                        |
                                        v
+--------------------------------------------------------------------------------------+
| Privacy, Ethics, and Memory Safety Controls                                          |
|                                                                                      |
| Techniques:                                                                          |
| - Data Anonymization: User = "alice", no PII stored                                  |
| - Controlled Local Storage: No cloud APIs used                                       |
| - TTL + Importance-driven memory compression                                         |
| - Optional: memory["sensitivity"] for conditional storage policies                   |
| - Secure ingestion layers (local Docker / API-gated)                                 |
+--------------------------------------------------------------------------------------+
```

## Directory Structure
```
.
├── core/
│   ├── app.py                 # Streamlit UI
│   ├── qdrant_ingest.py       # Qdrant memory ingestion
│   ├── duckdb_store.py        # DuckDB timeline storage
│   ├── neo4j_store.py         # Neo4j graph storage
│   ├── generate_response.py   # LLM+Memory vs LLM-only answers
│   ├── summarizer.py          # Memory summarization logic
│   ├── ingestion.py           # Deduplication + preprocessing
│   ├── retrieval.py           # Log relevance and scoring
│   ├── adaptive_forgetting.py # TTL and low-score discards
│   └── ...
├── data/
│   ├── memory_logs_with_duplicates.jsonl
│   └── filtered_memory_logs.jsonl
├── .env
├── requirements.txt
├── README.md
└── LICENSE
```
## Getting Started

### 1. Clone the Repository

git clone https://github.com/samhitasari05/memosynth-lite.git
cd memosynth-lite

2. Create Virtual Environment & Install Dependencies

python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

3. Start Qdrant & Neo4j Locally
Qdrant (Vector DB):
docker run -p 6333:6333 qdrant/qdrant

Neo4j (Graph DB):
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/test neo4j

DuckDB (Timeline Memory):

No server or container needed. DuckDB runs directly from Python and automatically creates the memory_timeline.duckdb file when you run the script.

Logs will be stored in DuckDB by running:

4. Generate & Ingest Logs
python generate/synthetic_logs.py
python core/qdrant_ingest.py
python core/duckdb_store.py
python core/neo4j_store.py

5. Launch the App
streamlit run core/app.py

---

## 🧠 DuckDB Timeline Memory Layer

The timeline layer in DuckDB provides a structured, queryable view of memory logs across time. This is crucial for answering questions like:

- “What happened in Project X during April?”
- “Summarize all feedback in March.”
- “Retrieve decision-type memories made last quarter.”

### ✅ Features

- Fast, local analytics for log-based queries
- Tracks timestamps, sessions, types, and project scopes
- Automatically updated via ingestion pipeline (`duckdb_store.py`)
- Supports future extensions like TTL expiry flags or importance labels

### 🗃️ Schema
TABLE: timeline_logs
| Field       | Type      | Description                            |
| ----------- | --------- | -------------------------------------- |
| log\_id     | TEXT      | Unique ID of the log                   |
| timestamp   | TIMESTAMP | Date and time when the event occurred  |
| user        | TEXT      | Author of the log                      |
| project     | TEXT      | Project or topic name                  |
| type        | TEXT      | Memory type (e.g., decision, feedback) |
| content     | TEXT      | Main content of the memory             |
| session\_id | TEXT      | Session identifier                     |


### 🛠️ How It Works

- On running `duckdb_store.py`, the logs from your JSONL file are loaded into DuckDB using parameterized inserts.
- The table `timeline_logs` is created if it doesn’t already exist.
- Logs are deduplicated (if filtered before) and persistently stored for future filtering, summarization, or querying.

---

###  Module Descriptions

| File                     | Description                                                                                          |
| ------------------------ | ---------------------------------------------------------------------------------------------------- |
| `synthetic_logs.py`      | Generates 300+ synthetic logs with memory types, timestamps, duplicates, and historic impact entries |
| `qdrant_ingest.py`       | Encodes content using `MiniLM`, stores semantic vectors in Qdrant with payloads                      |
| `duckdb_store.py`        | Inserts structured logs with timestamps into DuckDB for timeline-based access                        |
| `neo4j_store.py`         | Creates memory graphs linking logs to users, types, sessions, and projects                           |
| `summarizer.py`          | Identifies logs older than 30 days, summarizes them using GPT-4o, and inserts back into Qdrant       |
| `generate_response.py`   | Retrieves logs from all sources and forms augmented prompts with LLM answer comparison               |
| `adaptive_forgetting.py` | Implements logic for forgetting logs post-summary, based on TTL or similarity scores                 |
| `app.py`                 | Streamlit frontend to ask queries, view memory logs, and compare answers visually                    |

--------

### Sample Output UI

Input: "Why was Project Atlas delayed in March?"

Output: Side-by-side comparison:

Raw LLM Answer (based on prompt only)

Memory-enhanced Answer (contextualized with logs)

Features:

Retrieved logs tagged by source (Qdrant/Neo4j/DuckDB)

Summary logs collapsed by default

Plotly chart for memory relevance scores

Discarded logs shown below main results

---------

### DuckDB Timeline Memory

Timeline memory helps answer questions like:

"What happened last month?"

"Summarize all decisions from Project Atlas."

| Field       | Type      | Description                            |
| ----------- | --------- | -------------------------------------- |
| log\_id     | TEXT      | Unique ID of the log                   |
| timestamp   | TIMESTAMP | Date and time when the event occurred  |
| user        | TEXT      | Author of the log                      |
| project     | TEXT      | Project or topic name                  |
| type        | TEXT      | Memory type (e.g., decision, feedback) |
| content     | TEXT      | Main content of the memory             |
| session\_id | TEXT      | Session identifier                     |

----

### Privacy & Security Considerations

Logs contain synthetic data only (e.g., "alice")

All processing is local — no OpenAI keys required

Memory logs support TTL expiration & summarization

Supports future sensitivity-based storage policies

No external API log storage — ensures confidentiality

-----

### Future Work

Slack/Notion log integration

Manual tagging and deletion (“Forget this” feature)

Sensitivity-aware memory storage

Long-term memory decay logic

Named-entity summary views (e.g., per customer)

---

### Known Limitations

Batch summarization only — not real-time

Neo4j currently stores only basic log connections

Not optimized for very large-scale memory yet

UI filters limited to project/type (for now)



