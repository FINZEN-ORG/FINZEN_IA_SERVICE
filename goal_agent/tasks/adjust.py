"""Task to handle ADJUST_GOALS action."""
from typing import Dict, Any, List
from ..prompts import ADJUST_PROMPT
from ..openai_wrapper import call_chat
from ..tools.episodic_tools import record_episodic_event, query_episodic_memory, get_recent_episodic_payloads
from ..tools.goals_tools import load_goals_from_input, get_monthly_surplus
from ..tools.atr import compute_atr
from ..utils.logging import get_logger
import json
from ..utils.json_utils import safe_parse_json

logger = get_logger("task_adjust")


def run(input_json: Dict[str, Any]) -> Dict[str, Any]:
    user_id = input_json.get("user_id")
    # Support both flat and nested financial_context shapes
    monthly_surplus = get_monthly_surplus(input_json)

    goals = load_goals_from_input(input_json)
    episodic = query_episodic_memory(user_id)
    recent_payloads = get_recent_episodic_payloads(user_id, n=5)

    # Compute ATRs
    atrs = [compute_atr(g) for g in goals]

    # Prepare LLM context for human-friendly reasoning
    context = {"monthly_surplus": monthly_surplus, "goals_count": len(goals), "atrs": atrs, "episodic_samples": recent_payloads}
    prompt = ADJUST_PROMPT + "\nContext:\n" + json.dumps(context, ensure_ascii=False)

    # Let LLM propose allocations but also compute deterministic allocation here to ensure consistency
    allocations = []
    surplus_used = 0.0

    # Deterministic allocation according to rule-of-thumb
    # classify each goal
    buckets = {"very_late": [], "late": [], "slightly_late": [], "balanced": [], "ahead": []}
    for a in atrs:
        cls = a.get("classification")
        gid = a.get("goal_id")
        if cls == "muy_atrasada":
            buckets.setdefault("very_late", []).append(a)
        elif cls == "atrasada":
            buckets.setdefault("late", []).append(a)
        elif cls == "ligeramente_atrasada":
            buckets.setdefault("slightly_late", []).append(a)
        elif cls == "equilibrada":
            buckets.setdefault("balanced", []).append(a)
        else:
            buckets.setdefault("ahead", []).append(a)

    # Allocation percentages
    pct_for_atrasadas = 0.5
    pct_for_equilibradas = 0.3
    pct_for_adelantadas = 0.2

    def allocate_to_group(group_list, amount_for_group):
        nonlocal surplus_used, allocations
        if not group_list or amount_for_group <= 0:
            return
        per_goal = amount_for_group / len(group_list)
        for g in group_list:
            allocations.append({
                "goal_id": int(g.get("goal_id")),
                "allocated_amount": round(per_goal, 2),
                "reason": f"Asignación automática para {g.get('classification')} (ATR={g.get('atr'):.2f})"
            })
            surplus_used += per_goal

    allocate_to_group(buckets.get("very_late", []) + buckets.get("late", []), monthly_surplus * pct_for_atrasadas)
    allocate_to_group(buckets.get("balanced", []), monthly_surplus * pct_for_equilibradas)
    allocate_to_group(buckets.get("ahead", []), monthly_surplus * pct_for_adelantadas)

    # Ensure every goal gets at least a minimal positive allocation (e.g., 1% of surplus equally)
    if goals and monthly_surplus > 0:
        min_each = max(1.0, (monthly_surplus * 0.01) )
        for g in goals:
            gid = int(g.get("id")) if g.get("id") is not None else None
            # skip if already has allocation
            if any(a["goal_id"] == gid for a in allocations):
                continue
            allocations.append({"goal_id": gid, "allocated_amount": round(min_each,2), "reason": "Allocation mínima para mantener avance"})
            surplus_used += min_each

    emotional_message = "Gran trabajo este mes. Tus metas siguen avanzando de forma sostenible y sin presión."

    result = {"adjustments": allocations, "surplus_used": round(surplus_used,2), "emotional_message": emotional_message}

    # Let LLM produce human explanation (best-effort, non-blocking)
    try:
        llm_resp = call_chat(prompt)
        # attempt to parse or ignore
        _ = safe_parse_json(llm_resp)
    except Exception:
        logger.debug("Adjust LLM call failed; continuing with deterministic allocations")

    record_episodic_event(user_id=user_id, event_type="ADJUST_GOALS", payload_in=input_json, payload_out=result, description="Ajuste automático de metas con excedente")

    return result
