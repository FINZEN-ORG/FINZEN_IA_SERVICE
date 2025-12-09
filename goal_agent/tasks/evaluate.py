"""Task to handle EVALUATE_GOAL action."""
from typing import Dict, Any
from ..prompts import EVALUATE_PROMPT
from ..openai_wrapper import call_chat
from ..tools.episodic_tools import record_episodic_event, query_episodic_memory, get_recent_episodic_payloads
from ..tools.goals_tools import load_goals_from_input, get_financial_context
from ..utils.logging import get_logger
import json
from ..utils.json_utils import safe_parse_json

logger = get_logger("task_evaluate")


def run(input_json: Dict[str, Any]) -> Dict[str, Any]:
    user_id = input_json.get("user_id")
    new_goal = input_json.get("new_goal_proposal")
    if not new_goal:
        logger.error("No new_goal_proposal provided for EVALUATE_GOAL")
        out = {"viable": False, "reason": "No proposal provided", "suggested_adjustments": None}
        record_episodic_event(user_id=user_id, event_type="EVALUATE_GOAL", payload_in=input_json, payload_out=out, description="Evaluation failed: missing proposal")
        return out

    semantic = input_json.get("semantic_memory") or {}
    financial_ctx = get_financial_context(input_json)
    existing_goals = load_goals_from_input(input_json)
    episodic = query_episodic_memory(user_id)
    recent_payloads = get_recent_episodic_payloads(user_id, n=5)

    context = {
        "new_goal": new_goal,
        "financial_context": financial_ctx,
        "semantic_memory": semantic,
        "existing_goals_count": len(existing_goals),
        "episodic_samples_count": len(episodic),
        "episodic_samples": recent_payloads,
    }

    prompt = EVALUATE_PROMPT + "\nContext:\n" + json.dumps(context, ensure_ascii=False)

    try:
        resp_text = call_chat(prompt)
        resp_json = safe_parse_json(resp_text)
        if resp_json is None:
            logger.debug("Evaluate task: raw LLM response (unparseable): %s", resp_text)
            followup = (
                "La respuesta anterior no era JSON válido. Responde SOLO con un JSON que cumpla el esquema:"
                " {\"viable\": true|false, \"reason\": \"...\", \"suggested_adjustments\": {...}}"
            )
            resp_text2 = call_chat(followup)
            logger.debug("Evaluate task: followup raw LLM response: %s", resp_text2)
            resp_json = safe_parse_json(resp_text2)

        if resp_json is None:
            logger.exception("Evaluation LLM error or unparseable response")
            resp_json = {"viable": False, "reason": "LLM error or unparseable response", "suggested_adjustments": None}
    except Exception:
        logger.exception("Evaluation LLM error")
        resp_json = {"viable": False, "reason": "LLM error", "suggested_adjustments": None}

    record_episodic_event(user_id=user_id, event_type="EVALUATE_GOAL", payload_in=input_json, payload_out=resp_json, description="Evaluación de viabilidad de meta")
    return resp_json
