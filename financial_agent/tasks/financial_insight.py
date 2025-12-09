import json
from datetime import datetime
from typing import Dict, Any
from ..models.schemas import OrchestratorInput, AgentOutput
from ..openai_wrapper import call_chat
from ..db import insert_episodic_record, query_episodic_by_user
from .. import prompts
from ..utils.logging import get_logger

logger = get_logger("financial_insight_task")

SYSTEM_JSON_ONLY = "You are a system assistant that must output valid JSON only. Do not output any other text."


def _call_prompt(prompt_text: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    full_prompt = prompt_text + "\n\nContext Payload:\n" + json.dumps(payload, default=str, ensure_ascii=False)
    logger.debug("Calling model with prompt length=%d", len(full_prompt))
    resp = call_chat(full_prompt, temperature=0.0, max_tokens=800, system_message=SYSTEM_JSON_ONLY)
    try:
        parsed = json.loads(resp)
        return parsed
    except Exception as e:
        logger.exception("Failed to parse model JSON response. Returning raw text in 'raw' key.")
        return {"raw": resp}


def _make_episodic_record(user_id: str, event_type: str, input_payload: Dict[str, Any], output_payload: Dict[str, Any], used_tone: str | None = None) -> Dict[str, Any]:
    uid = None
    try:
        if isinstance(user_id, int):
            uid = user_id
        elif isinstance(user_id, str):
            if user_id.isdigit():
                uid = int(user_id)
            else:
                digits = ''.join(ch for ch in user_id if ch.isdigit())
                uid = int(digits) if digits else None
    except Exception:
        uid = None

    record = {
        "user_id": uid if uid is not None else user_id,
        "agent_name": "financial_insight_agent",
        "event_type": event_type,
        "input_payload": input_payload,
        "semantic_snapshot": input_payload.get("semantic_memory"),
        "episodic_context": None,
        "output_payload": output_payload,
        "used_tone": used_tone,
    }
    return record


def run_orchestrator(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main entrypoint for the task. Validates input and runs requested mode(s)."""
    try:
        orch = OrchestratorInput(**input_data)
    except Exception as e:
        logger.exception("Invalid input payload")
        return {"status": "error", "message": "invalid input"}

    mode = orch.mode
    user_id = orch.user_id
    event_type = mode
    episodic = query_episodic_by_user(user_id, limit=200)

    payload_base = {
        "semantic_memory": orch.semantic_memory,
        "financial_context": orch.financial_context.dict(),
        "transactions": [t.dict() for t in orch.transactions],
        "goals": orch.goals,
        "episodic_memory_snapshot": episodic,
    }

    insights = {}

    if mode in ("ants", "all"):
        out_ants = _call_prompt(prompts.ANT_EXPENSES_PROMPT, payload_base)
        insights["ants"] = out_ants

    if mode in ("repetitive", "all"):
        out_rep = _call_prompt(prompts.REPETITIVE_EXPENSES_PROMPT, payload_base)
        insights["repetitive"] = out_rep

    if mode in ("health", "all"):
        out_health = _call_prompt(prompts.HEALTH_PROMPT, payload_base)
        insights["health"] = out_health

    if mode in ("leaks", "all"):
        out_leaks = _call_prompt(prompts.LEAKS_PROMPT, payload_base)
        insights["leaks"] = out_leaks

    if mode == "single" and not insights:
        out_health = _call_prompt(prompts.HEALTH_PROMPT, payload_base)
        insights["health"] = out_health

    output_payload = {
        "status": "success",
        "mode": mode,
        "insights": insights,
        "episodic_record_created": False,
    }

    try:
        record = _make_episodic_record(user_id=user_id, event_type=event_type, input_payload=input_data, output_payload=output_payload, used_tone=None)
        res = insert_episodic_record(record)
        output_payload["episodic_record_created"] = True
        output_payload["episodic_record_id"] = res.get("inserted_id")
    except Exception:
        logger.exception("Failed to persist episodic record")
        output_payload["episodic_record_created"] = False

    return output_payload


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        import json
        data = json.loads(sys.argv[1])
        print(json.dumps(run_orchestrator(data), default=str, indent=2))
    else:
        print("Run programmatically by calling run_orchestrator(...) with orchestrator payload")
