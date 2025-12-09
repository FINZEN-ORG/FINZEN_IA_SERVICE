import argparse
import json
from .agent import handle_message
from .utils.logging import get_logger

logger = get_logger("financial_agent_runner")

EXAMPLES = {
    "ants": {
        "mode": "ants",
        "event_type": "ANT_EXPENSES_PROMPT",
        "user_id": 123,
        "semantic_memory": {"habits": ["buys coffee daily", "snacks at work"]},
        "financial_context": {"monthly_income": 3000, "fixed_expenses": 1200, "variable_expenses": 900, "savings": 300, "month_surplus": 600},
        "transactions": [
            {"id":"a1","amount":3.25,"category_id":"coffee","description":"coffee","date":"2025-11-29T08:01:00Z","type":"expense"},
            {"id":"a2","amount":2.75,"category_id":"snack","description":"chips","date":"2025-11-29T10:30:00Z","type":"expense"}
        ],
        "goals": ["save for vacation"]
    },
    "repetitive": {
        "mode": "repetitive",
        "event_type": "REPETITIVE_EXPENSES_PROMPT",
        "user_id": 123,
        "semantic_memory": {"subscriptions": ["music_streaming"]},
        "financial_context": {"monthly_income": 3000, "fixed_expenses": 1500, "variable_expenses": 800, "savings": 200, "month_surplus": 500},
        "transactions": [
            {"id":"s1","amount":9.99,"category_id":"subscription","description":"Music Premium","date":"2025-11-01T00:00:00Z","type":"expense"},
            {"id":"s2","amount":9.99,"category_id":"subscription","description":"Music Premium","date":"2025-10-01T00:00:00Z","type":"expense"}
        ],
        "goals": []
    },
    "health": {
        "mode": "health",
        "event_type": "HEALTH_PROMPT",
        "user_id": 123,
        "semantic_memory": {"financial_summary": {"risk_profile": "moderate"}},
        "financial_context": {"monthly_income": 3000, "fixed_expenses": 1400, "variable_expenses": 900, "savings": 100, "month_surplus": 600},
        "transactions": [
            {"id":"t1","amount":1200,"category_id":"rent","description":"monthly rent","date":"2025-11-01T00:00:00Z","type":"expense"},
            {"id":"t2","amount":150,"category_id":"groceries","description":"supermarket","date":"2025-11-05T00:00:00Z","type":"expense"}
        ],
        "goals": [{"id":"g1","name":"Emergency Fund","saved_amount":300,"target_amount":2000}]
    },
    "leaks": {
        "mode": "leaks",
        "event_type": "LEAKS_PROMPT",
        "user_id": 123,
        "semantic_memory": {"recent_events": ["trip spending spike"]},
        "financial_context": {"monthly_income": 3000, "fixed_expenses": 1300, "variable_expenses": 1000, "savings": 200, "month_surplus": 500},
        "transactions": [
            {"id":"p1","amount":1200,"category_id":"travel","description":"flight ticket","date":"2025-11-15T00:00:00Z","type":"expense"},
            {"id":"p2","amount":80,"category_id":"transport","description":"extra taxi","date":"2025-11-16T00:00:00Z","type":"expense"}
        ],
        "goals": []
    },
    "all": {
        "mode": "all",
        "event_type": "FULL_ANALYSIS_PROMPT",
        "user_id": 123,
        "semantic_memory": {"habits": ["coffee daily"], "subscriptions": ["music_streaming"]},
        "financial_context": {"monthly_income": 3000, "fixed_expenses": 1400, "variable_expenses": 900, "savings": 200, "month_surplus": 500},
        "transactions": [
            {"id":"t1","amount":3.5,"category_id":"coffee","description":"latte","date":"2025-11-28T09:00:00Z","type":"expense"},
            {"id":"s1","amount":9.99,"category_id":"subscription","description":"Music Premium","date":"2025-11-01T00:00:00Z","type":"expense"},
            {"id":"p1","amount":1200,"category_id":"travel","description":"flight","date":"2025-11-15T00:00:00Z","type":"expense"}
        ],
        "goals": [{"id":"g1","name":"Vacation","saved_amount":400,"target_amount":2000}]
    },
    "single_health": {
        "mode": "single",
        "event_type": "HEALTH_PROMPT",
        "user_id": 123,
        "semantic_memory": {},
        "financial_context": {"monthly_income": 3000, "fixed_expenses": 1200, "variable_expenses": 800, "savings": 200, "month_surplus": 800},
        "transactions": [],
        "goals": []
    }
}


def run_examples(selected: list[str] | None = None) -> None:
    keys = list(EXAMPLES.keys()) if not selected else selected
    for k in keys:
        sample = EXAMPLES.get(k)
        if sample is None:
            print(f"No example named {k}")
            continue
        print("\n=== Running example:", k, "===")
        try:
            out = handle_message(sample)
            print(json.dumps(out, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.exception("Example %s failed", k)
            print(f"Example {k} failed: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--examples", "-e", action="store_true", help="Run builtin example inputs for financial agent")
    parser.add_argument("--which", "-w", nargs="*", help="Run only selected examples by key (ants repetitive health leaks all single_health)")
    args = parser.parse_args()

    if args.examples:
        run_examples(args.which)
    else:
        print("Run with --examples to execute builtin example inputs, or edit the file to add more tests.")


if __name__ == "__main__":
    main()
