"""Tools to read and write episodic memory.

Implements: query_episodic_memory(user_id) and record_episodic_event(...)
"""
from typing import Dict, Any, List
from .. import db
from ..utils.logging import get_logger
from ..utils.date_utils import now_utc, isoformat

logger = get_logger("episodic_tools")


def query_episodic_memory(user_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    try:
        return db.query_episodic_by_user(user_id, limit=limit)
    except Exception as e:
        logger.exception("Failed to query episodic memory")
        return []


def record_episodic_event(user_id: str, event_type: str, payload_in: Dict[str, Any], payload_out: Dict[str, Any], description: str) -> Dict[str, Any]:
    record = {
        "user_id": str(user_id),
        # goal_name in DB is NOT NULL; prefer new_goal_proposal.name, else fallback to action or a default
        "goal_name": (
            (payload_in or {}).get("new_goal_proposal", {}).get("name")
            or (payload_in or {}).get("action")
            or "general"
        ),
        "event_type": event_type,
        "message": description,
        "parameters": {"payload_in": payload_in, "payload_out": payload_out},
        "created_at": isoformat(now_utc()),
    }
    try:
        res = db.insert_episodic_record(record)
        logger.info("Recorded episodic event id=%s for user=%s", res.get("inserted_id"), user_id)
        return res
    except Exception:
        logger.exception("Unable to record episodic event")
        return {"error": "failed"}


def get_recent_episodic_payloads(user_id: str, n: int = 5) -> List[Dict[str, Any]]:
    """Return the last `n` episodic records for user_id with only the most relevant fields.

    The returned items contain: id, event_type, created_at, and parameters (payload_in, payload_out).
    """
    try:
        rows = query_episodic_memory(user_id, limit=n)
        samples = []
        for r in rows:
            created = r.get("created_at")
            # convert datetimes to ISO strings for safe JSON serialization
            try:
                if hasattr(created, "isoformat"):
                    created_val = created.isoformat()
                else:
                    created_val = created
            except Exception:
                created_val = created
            samples.append({
                "id": r.get("id"),
                "event_type": r.get("event_type"),
                "created_at": created_val,
                "parameters": r.get("parameters"),
            })
        return samples
    except Exception:
        logger.exception("Failed to get recent episodic payloads")
        return []
