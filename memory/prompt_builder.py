# core/prompt_builder.py

def build_prompt(query, logs):
    """
    Build a prompt to guide the LLM in answering the user's query using context from memory logs.
    """
    context_blocks = []
    for i, log in enumerate(logs, 1):
        timestamp = log.get("timestamp", "Unknown")
        speaker = log.get("user", "Unknown")
        content = log.get("content", "").strip()
        project = log.get("project", "Unknown")
        log_type = log.get("type", "general").capitalize()
        source = log.get("source", "unknown").upper()

        entry = (
            f"[Log {i} | {timestamp} | Project: {project} | Source: {source} | Type: {log_type}]\n"
            f"{speaker}: {content}"
        )
        context_blocks.append(entry)

    context_text = "\n\n".join(context_blocks)

    prompt = f"""
You are an AI assistant helping a product team analyze historical discussions, summaries, and decisions from logs.

Use the logs below to answer the user's question. Your answer should:
- Be grounded in the evidence provided.
- Combine relevant information from multiple logs.
- Mention specific reasons, discussions, or stakeholders if found.
- Avoid vague or general responses.

User Question:
"{query}"

Memory Logs:
{context_text}

Based on this, provide a clear and informative answer.
If no answer is possible, say so honestly.
"""

    return prompt.strip()
