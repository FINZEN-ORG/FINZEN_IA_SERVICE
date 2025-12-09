"""Task to handle TRACK_GOAL action."""
from typing import Dict, Any
from ..prompts import TRACK_PROMPT
from ..openai_wrapper import call_chat
from ..tools.goals_tools import get_goal_by_id, load_goals_from_input, get_monthly_surplus
from ..tools.episodic_tools import record_episodic_event, query_episodic_memory, get_recent_episodic_payloads
from ..tools.atr import compute_atr
from ..utils.logging import get_logger
import json
from ..utils.json_utils import safe_parse_json

logger = get_logger("task_track")


def run(input_json: Dict[str, Any]) -> Dict[str, Any]:
    user_id = input_json.get("user_id")
    goals = load_goals_from_input(input_json)
    goal_id = input_json.get("goal_id")
    if not goal_id:
        out = {"error": "goal_id required"}
        record_episodic_event(user_id=user_id, event_type="TRACK_GOAL", payload_in=input_json, payload_out=out, description="Tracking failed: missing goal_id")
        return out

    goal = get_goal_by_id(goals, goal_id)
    if not goal:
        out = {"error": "goal not found in provided goals"}
        record_episodic_event(user_id=user_id, event_type="TRACK_GOAL", payload_in=input_json, payload_out=out, description="Tracking failed: goal missing")
        return out

    # compute ATR and projection
    atr_info = compute_atr(goal)
    # include recent episodic payloads for context
    recent_payloads = get_recent_episodic_payloads(user_id, n=5)

    # naive projection: assume monthly surplus applied to this goal proportionally
    monthly_surplus = get_monthly_surplus(input_json)
    # estimate months remaining
    from dateutil import parser
    from datetime import datetime
    try:
        due = parser.isoparse(goal.get("due_date")) if goal.get("due_date") else None
        now = datetime.utcnow()
        months_left = max(0.1, (due - now).days / 30) if due else 12
    except Exception:
        months_left = 12

    try:
        saved = float(goal.get("saved_amount", 0))
        target = float(goal.get("target_amount", 0))
    except Exception:
        saved = 0.0
        target = 0.0

    expected_savings_by_due_date = saved + monthly_surplus * months_left
    # risk heuristic
    ratio = (expected_savings_by_due_date / target) if target > 0 else 0
    if ratio >= 1.0:
        risk = "low"
        status = "on_track"
        message = "¡Vas muy bien! Mantén el ritmo actual."
    elif ratio >= 0.7:
        risk = "medium"
        status = "behind"
        message = "Estás cerca, considera ajustes pequeños o incrementar ahorros." 
    else:
        risk = "high"
        status = "critical"
        message = "Necesitas replantear la meta o mejorar tus finanzas para evitar frustración."

    out = {
        "goal_id": int(goal_id),
        "status": status,
        "message": message,
        "projections": {
            "expected_savings_by_due_date": round(expected_savings_by_due_date, 2),
            "risk_level": risk,
            "atr": round(atr_info.get("atr", 0), 2)
        }
    }

    # Optionally include the recent payloads in the output for transparency
    out["episodic_samples"] = recent_payloads

    record_episodic_event(user_id=user_id, event_type="TRACK_GOAL", payload_in=input_json, payload_out=out, description="Seguimiento individual de meta")

    return out
