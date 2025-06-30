from collections import Counter
import json

# Update this path to your actual file location
input_path = "../data/memory_logs_with_historic_impact.jsonl"

# Load logs
with open(input_path, "r") as f:
    logs = [json.loads(line) for line in f]

# Count duplicate content
content_counts = Counter(log["content"] for log in logs)

# Find duplicates
duplicates = {text: count for text, count in content_counts.items() if count > 1}

# Summary
print(f"Total logs: {len(logs)}")
print(f"Unique content entries: {len(content_counts)}")
print(f"Duplicate entries (by content): {len(duplicates)}")
print("\nSample duplicate contents and their counts:")
for i, (text, count) in enumerate(duplicates.items()):
    print(f"{i+1}. {count}x - {text}")
    if i == 4:  # Show only first 5
        break
