"""Tools to query and manipulate user goals.

Note: This module expects that goals are available either from the incoming JSON or from a separate goals DB.
For portability we accept goals passed in the orchestrator input; if not present, this tool returns an empty list.
"""
from typing import List, Dict, Any, Optional
from ..utils.logging import get_logger

logger = get_logger("goals_tools")


def load_goals_from_input(input_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Load goals from input JSON accepting multiple possible field names.

    Supported locations (in order):
    - input_json['goals']
    - input_json['existing_goals']
    - input_json['analysis_context']['goals']

    Returns an empty list if none found.
    """
    if not input_json or not isinstance(input_json, dict):
        logger.info("Invalid input_json for load_goals_from_input")
        return []

    goals = input_json.get("goals")
    if not goals:
        goals = input_json.get("existing_goals")
    if not goals:
        analysis = input_json.get("analysis_context") or {}
        goals = analysis.get("goals") if isinstance(analysis, dict) else None

    if not goals:
        logger.info("No goals found in input JSON; returning empty list")
        return []

    # Normalize each goal to be a dict with string keys and try to coerce numeric values
    normalized = []
    for g in goals:
        if not isinstance(g, dict):
            continue
        # ensure id exists as string or int
        normalized.append(g)

    return normalized


def get_goal_by_id(goals: List[Dict[str, Any]], goal_id: Any) -> Dict[str, Any]:
    """Return a single goal by id from a list of goals, tolerant to string/int ids."""
    if not goals:
        return {}
    for g in goals:
        try:
            if g is None:
                continue
            if g.get("id") is None:
                continue
            if int(str(g.get("id"))) == int(str(goal_id)):
                return g
        except Exception:
            continue
    return {}


def get_financial_context(input_json: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize financial context from multiple possible shapes into a flat dict.

    Expected normalized keys (when available):
    - monthly_income, fixed_expenses, variable_expenses, savings, monthly_surplus
    """
    ctx = {}
    raw = (input_json or {}).get("financial_context") or {}
    if not isinstance(raw, dict):
        return ctx

    # income may be nested
    income = raw.get("income") or {}
    if isinstance(income, dict):
        ctx["monthly_income"] = income.get("monthly_average") or income.get("monthly") or raw.get("monthly_income")
    else:
        ctx["monthly_income"] = raw.get("monthly_income") or raw.get("income")

    # expenses may be nested
    expenses = raw.get("expenses") or {}
    if isinstance(expenses, dict):
        ctx["fixed_expenses"] = expenses.get("fixed_monthly") or expenses.get("fixed_expenses")
        ctx["variable_expenses"] = expenses.get("variable_monthly_avg") or expenses.get("variable_expenses")
    else:
        ctx["fixed_expenses"] = raw.get("fixed_expenses")
        ctx["variable_expenses"] = raw.get("variable_expenses")

    # savings
    savings = raw.get("savings") or {}
    if isinstance(savings, dict):
        ctx["savings"] = savings.get("current_balance") or raw.get("savings")
    else:
        ctx["savings"] = raw.get("savings")

    # surplus can be nested under 'surplus' or top-level monthly_surplus
    surplus = raw.get("surplus") or {}
    if isinstance(surplus, dict):
        ctx["monthly_surplus"] = surplus.get("monthly") or raw.get("monthly_surplus") or raw.get("surplus_monthly")
    else:
        ctx["monthly_surplus"] = raw.get("monthly_surplus") or raw.get("surplus")

    # include raw for anything else
    ctx["_raw"] = raw
    return ctx


def get_monthly_surplus(input_json: Dict[str, Any]) -> float:
    fc = get_financial_context(input_json)
    try:
        return float(fc.get("monthly_surplus") or 0)
    except Exception:
        return 0.0


def load_transactions_from_input(input_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Load transactions accepting 'transactions' or 'recent_transactions'."""
    if not input_json or not isinstance(input_json, dict):
        return []
    tx = input_json.get("transactions") or input_json.get("recent_transactions")
    if not tx:
        analysis = input_json.get("analysis_context") or {}
        if isinstance(analysis, dict):
            tx = analysis.get("transactions") or analysis.get("recent_transactions")
    if not tx:
        return []
    return [t for t in tx if isinstance(t, dict)]
