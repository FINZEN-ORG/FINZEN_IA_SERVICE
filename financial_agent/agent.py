"""Top-level agent API for Financial Insight Agent."""
from .tasks.financial_insight import run_orchestrator


def handle_message(payload: dict) -> dict:
    """Entrypoint compatible with orchestrator: accepts dict, returns dict."""
    return run_orchestrator(payload)
