# core/generate_response.py

import os
import ast
from openai import OpenAI
from retrieval import get_combined_logs
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def clean_response(text):
    text = text.strip()
    if text.startswith("(") or text.startswith("["):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, (list, tuple)):
                return parsed[-1].strip()
        except Exception:
            pass
    return text

def build_structured_prompt(query, logs):
    lines = [f"User Query: {query}\n\n", "Here are relevant memory logs:\n"]
    for i, log in enumerate(logs, 1):
        speaker = log.get("user", "Unknown")
        content = log.get("content", "No content.")
        timestamp = log.get("timestamp", "Unknown time")
        lines.append(f"Log {i} ({timestamp}) | Speaker: {speaker}\n{content}\n")

    lines.append(
        "\nPlease provide a well-grounded, confident response using the logs above. "
        "If multiple logs support a point, cite them (e.g., 'as noted in Log 2'). "
        "Avoid hedging unless memory logs are unclear."
    )
    return "\n".join(lines)

def generate_response(query, debug=False):
    logs = get_combined_logs(query)  # scored logs

    if debug:
        print("Top Relevant Logs:")
        for i, log in enumerate(logs):
            score = round(log.get("score", 0), 4)
            content = log.get("content", "")[:120].strip().replace("\n", " ")
            print(f"Log {i+1} | Score: {score} | {content}...")

    memory_prompt = build_structured_prompt(query, logs)

    # Memory-grounded response
    memory_response_raw = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant with access to memory logs. "
                    "Use the logs to generate a factual, confident answer. "
                    "Cite logs clearly (e.g., 'Log 2') and avoid speculation if logs are strong."
                ),
            },
            {"role": "user", "content": memory_prompt},
        ]
    ).choices[0].message.content

    # Raw response without memory
    raw_response_raw = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": query},
        ]
    ).choices[0].message.content

    return clean_response(raw_response_raw), clean_response(memory_response_raw)

if __name__ == "__main__":
    user_query = input("Ask a question: ")
    raw, grounded = generate_response(user_query, debug=True)

    print("\nLLM Only:\n", raw)
    print("\nLLM + Memory:\n", grounded)
