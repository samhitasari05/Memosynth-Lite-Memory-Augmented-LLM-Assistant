# check_speakers.py

import json

with open("../data/filtered_memory_logs.jsonl") as f:
    for i, line in enumerate(f, 1):
        log = json.loads(line)
        print(f"{i:03d}: {log.get('speaker', 'Missing')}")
