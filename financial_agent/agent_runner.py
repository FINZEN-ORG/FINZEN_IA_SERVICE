"""Simple runner for local debugging of the Financial Insight Agent."""
import json
from .agent import handle_message


def run_from_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    out = handle_message(payload)
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m financial_agent.agent_runner <input.json>")
    else:
        run_from_file(sys.argv[1])
