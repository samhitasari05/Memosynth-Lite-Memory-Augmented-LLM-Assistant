from retrieval import get_combined_logs
from dotenv import load_dotenv
load_dotenv()

query = "What did Carol say about Analytics Dashboard?"
logs = get_combined_logs(query)

for log in logs:
    print(f"[{log['timestamp']}] {log['user']} said: {log['content']}")
