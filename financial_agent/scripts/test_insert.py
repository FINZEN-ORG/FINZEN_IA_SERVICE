"""Test script to verify insert into episodic_memory_financial.

Usage:
  python financial_agent/scripts/test_insert.py

This will attempt to insert a minimal record and print the result or the
exception traceback so you can see why an insert might be failing.
"""
import json
import traceback
from datetime import datetime

from financial_agent.db import insert_episodic_record


def make_sample_record():
    return {
        "user_id": 123,
        "agent_name": "financial_insight_agent",
        "event_type": "health",
        "input_payload": {"test": True, "timestamp": datetime.utcnow().isoformat()},
        "semantic_snapshot": {"notes": ["test insert"]},
        "episodic_context": None,
        "output_payload": {"status": "ok", "sample": True},
        "used_tone": None,
    }


def main():
    rec = make_sample_record()
    print("Attempting insert with record:")
    print(json.dumps(rec, default=str, indent=2, ensure_ascii=False))
    try:
        res = insert_episodic_record(rec)
        print("Insert result:", res)
    except Exception:
        print("Insert failed with exception:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
