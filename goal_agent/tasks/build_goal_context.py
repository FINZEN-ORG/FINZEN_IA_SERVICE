"""Task to handle BUILD_GOAL_CONTEXT action.

Produces an enriched, deterministic context per goal (no LLM required).
"""
from typing import Dict, Any, List
from dateutil import parser
from datetime import datetime
from ..tools.goals_tools import load_goals_from_input, get_financial_context
from ..tools.atr import compute_atr
from ..tools.episodic_tools import record_episodic_event
from ..utils.logging import get_logger

logger = get_logger("task_build_goal_context")


def months_between(now: datetime, future: datetime) -> float:
    delta_days = (future - now).days
    return max(0.0, delta_days / 30.0)


def map_classification(spanish_cls: str) -> str:
    mapping = {
        "adelantada": "ahead",
        "equilibrada": "balanced",
        "ligeramente_atrasada": "slightly_behind",
        "atrasada": "behind",
        "muy_atrasada": "critical",
    }
    return mapping.get(spanish_cls, "balanced")


def run(input_json: Dict[str, Any]) -> Dict[str, Any]:
    user_id = input_json.get("user_id")
    goals = load_goals_from_input(input_json)
    fc = get_financial_context(input_json)

    now = datetime.utcnow()
    enriched: List[Dict[str, Any]] = []
    for g in goals:
        try:
            goal_id = int(g.get("id")) if g.get("id") is not None else None
            name = g.get("name")
            saved = float(g.get("saved_amount") or 0)
            target = float(g.get("target_amount") or 0)

            due = None
            try:
                due = parser.isoparse(g.get("due_date")) if g.get("due_date") else None
            except Exception:
                due = None

            remaining_months = months_between(now, due) if due else 0
            progress_ratio = (saved / target) if target > 0 else 0.0
            required_monthly_saving = 0.0
            if target > 0 and remaining_months > 0:
                required_monthly_saving = max(0.0, (target - saved) / remaining_months)

            atr_info = compute_atr(g)
            spanish_cls = atr_info.get("classification")
            status = map_classification(spanish_cls)

            time_risk = "low"
            if remaining_months <= 1:
                time_risk = "high"
            elif remaining_months <= 3:
                time_risk = "medium"

            enriched.append({
                "goal_id": goal_id,
                "name": name,
                "financial_state": {
                    "saved_amount": saved,
                    "target_amount": target,
                    "progress_ratio": round(progress_ratio, 4),
                    "required_monthly_saving": round(required_monthly_saving, 2),
                },
                "time_state": {
                    "due_date": g.get("due_date") or None,
                    "time_elapsed_ratio": round(atr_info.get("time_ratio", 0), 4),
                    "remaining_months": round(remaining_months, 2),
                },
                "performance": {
                    "status": status,
                    "time_risk": time_risk,
                },
                "emotional_guidance": {
                    "recommended_tone": (input_json.get("semantic_memory") or {}).get("motivation_profile", {}).get("preferred_tone", "encouragement"),
                    "avoid_pressure": True,
                },
            })
        except Exception:
            logger.exception("Failed to enrich goal: %s", g)
            continue

    out = {"goals_enriched_context": enriched}

    # record event for traceability
    try:
        record_episodic_event(user_id=user_id, event_type="BUILD_GOAL_CONTEXT", payload_in=input_json, payload_out=out, description="Enriched goal contexts generated")
    except Exception:
        logger.debug("Could not record episodic event for BUILD_GOAL_CONTEXT")

    return out
