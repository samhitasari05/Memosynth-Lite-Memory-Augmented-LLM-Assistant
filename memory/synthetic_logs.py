import json
import random
from datetime import datetime, timedelta
from faker import Faker
import uuid

fake = Faker()

# Configuration
num_current_logs = 300
num_old_logs = 60
duplicate_ratio = 0.10
output_path = "../data/memory_logs_with_historic_impact.jsonl"

memory_types = ["decision", "feedback", "ticket", "question", "summary", "milestone"]
projects = ["Onboarding Redesign", "AI Assistant", "Infra Migration", "Feature Flags", "Analytics Dashboard"]
users = ["alice", "bob", "carol", "dave", "eve"]

base_time = datetime(2024, 4, 1, 9, 0, 0)  

# Templates (same as before)
templates = {
    "decision": [
        "We agreed to postpone {} due to {}.",
        "The team decided to move forward with {} after reviewing {}.",
        "Finalized design for {} based on feedback about {}."
    ],
    "feedback": [
        "User reported that {} was unclear.",
        "Received feedback that {} needs improvement.",
        "Stakeholder mentioned {} was confusing."
    ],
    "ticket": [
        "Bug in {} caused unexpected {} behavior.",
        "Created a ticket to address issue with {}.",
        "Assigned ticket to {} for resolving {}."
    ],
    "question": [
        "What are the next steps for {}?",
        "How should we handle {} in the next sprint?",
        "Do we have any data on {} performance?"
    ],
    "summary": [
        "Meeting covered {} and discussed {}.",
        "Reviewed progress on {} and aligned on next steps.",
        "Key updates included {}, {}, and {}."
    ],
    "milestone": [
        "Released {} version of the {} feature.",
        "Completed testing phase for {}.",
        "{} reached production deployment."
    ]
}

def generate_log_entry(i, offset_minutes=13, base_date=base_time):
    memory_type = random.choice(memory_types)
    project = random.choice(projects)
    user = random.choice(users)
    session_id = f"sess_{random.randint(100, 999)}"
    timestamp = base_date + timedelta(minutes=i * offset_minutes)
    template = random.choice(templates[memory_type])
    placeholders = [fake.bs() for _ in range(template.count("{}"))]
    content = template.format(*placeholders)

    return {
        "timestamp": timestamp.isoformat(),
        "user": user,
        "project": project,
        "type": memory_type,
        "content": content,
        "session_id": session_id,
        "log_id": str(uuid.uuid4())
    }

def generate_impact_log(i):
    project = random.choice(projects)
    user = random.choice(users)
    session_id = f"sess_{random.randint(100, 999)}"
    ts = datetime(2024, 3, 1, 8, 0, 0) + timedelta(days=i)
    type_choice = random.choice(["summary", "milestone"])

    content = f"March revenue exceeded ${random.randint(50, 100)}K; {project} milestone reached in sprint {random.randint(5, 10)}."

    return {
        "timestamp": ts.isoformat(),
        "user": user,
        "project": project,
        "type": type_choice,
        "content": content,
        "session_id": session_id,
        "log_id": str(uuid.uuid4())
    }

# Step 1: Generate current logs
current_logs = [generate_log_entry(i) for i in range(num_current_logs)]

# Step 2: Generate old impactful logs
old_logs = [generate_impact_log(i) for i in range(num_old_logs)]

# Step 3: Add duplicates (10% of current logs)
duplicates = []
num_duplicates = int(duplicate_ratio * num_current_logs)
for entry in random.sample(current_logs, num_duplicates):
    dup = entry.copy()
    shifted_ts = datetime.fromisoformat(dup["timestamp"]) + timedelta(minutes=random.randint(-5, 5))
    dup["timestamp"] = shifted_ts.isoformat()
    dup["log_id"] = str(uuid.uuid4())
    duplicates.append(dup)

# Step 4: Combine all
all_logs = current_logs + old_logs + duplicates
random.shuffle(all_logs)

with open(output_path, "w") as f:
    for log in all_logs:
        f.write(json.dumps(log) + "\n")

print(f"Generated {len(current_logs)} recent logs, {len(old_logs)} old impact logs, and {len(duplicates)} duplicates.")
