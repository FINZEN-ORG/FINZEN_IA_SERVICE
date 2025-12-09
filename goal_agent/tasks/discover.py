"""Task to handle DISCOVER_GOALS action."""
from typing import Dict, Any
from ..prompts import DISCOVER_PROMPT
from ..openai_wrapper import call_chat
from ..tools.episodic_tools import record_episodic_event, query_episodic_memory, get_recent_episodic_payloads
from ..tools.goals_tools import load_goals_from_input, get_financial_context, load_transactions_from_input
from ..utils.logging import get_logger
from ..utils.json_utils import safe_parse_json
import json

logger = get_logger("task_discover")


def run(input_json: Dict[str, Any]) -> Dict[str, Any]:
    user_id = input_json.get("user_id")
    semantic = input_json.get("semantic_memory") or {}
    financial_ctx = get_financial_context(input_json)
    transactions = load_transactions_from_input(input_json)

    # Fetch episodic memory directly from Postgres
    episodic = query_episodic_memory(user_id)
    # include recent payloads (parameters) to provide richer context to the LLM
    recent_payloads = get_recent_episodic_payloads(user_id, n=5)

    # Build prompt with context
    context = {
        "semantic_memory": semantic,
        "financial_context": financial_ctx,
        "transactions": transactions,
        "episodic_samples_count": len(episodic),
        "episodic_samples": recent_payloads,
    }

    prompt = DISCOVER_PROMPT + "\nContext:\n" + json.dumps(context, ensure_ascii=False)

    # Strong system message to push the model to return JSON only
    system_msg = (
        "Eres un sistema que RESPONDE SOLO con JSON. "
        "No añadas explicaciones, no uses comillas triples ni formato adicional. "
        "Si no puedes, responde un JSON vacío válido."
    )

    resp_json = None
    last_raw = None
    # Try up to 3 attempts: initial call + two clarifying followups
    for attempt in range(1, 4):
        try:
            logger.debug("Discover task: LLM call attempt %d/3", attempt)
            # send system message on all attempts
            resp_text = call_chat(prompt if attempt == 1 else followup_text, system_message=system_msg) if attempt > 1 else call_chat(prompt, system_message=system_msg)
            last_raw = resp_text
            logger.debug("Discover task: raw LLM response (attempt %d): %s", attempt, resp_text)
            resp_json = safe_parse_json(resp_text)
            if resp_json is not None:
                break

            # prepare followup for next attempt that includes previous raw text
            followup_text = (
                "La respuesta anterior no era JSON válido. Aquí está la respuesta previa delimitada entre >>> y <<<. "
                "Extrae y devuelve SOLO el JSON que cumpla este esquema EXACTO:"
                " {\"suggested_goals\": [{\"name\": \"...\", \"reason\": \"...\", \"estimated_target\": 0, \"suggested_timeframe\": \"...\"}]}"
                "\n>>>" + (last_raw or "") + "<<<"
            )
            # next loop will call call_chat with followup_text
        except Exception:
            logger.exception("Discover task failed to get JSON from LLM on attempt %d", attempt)
            resp_json = None

    if resp_json is None:
        logger.error("Discover task: LLM did not return parseable JSON after retries; falling back to empty list")
        resp_json = {"suggested_goals": []}

    # Record episodic memory
    out = record_episodic_event(user_id=user_id, event_type="DISCOVER_GOALS", payload_in=input_json, payload_out=resp_json, description="Sugerencias de nuevas metas generadas")

    return resp_json
