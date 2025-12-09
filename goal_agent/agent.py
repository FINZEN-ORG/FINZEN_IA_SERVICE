"""Goal Intelligence Agent wiring tasks and tools with CrewAI-like interface.

This module exposes `handle(input_json)` which the Orchestrator can call.
"""
from typing import Dict, Any
from .tasks import discover, evaluate, adjust, track, build_goal_context
from .utils.logging import get_logger

logger = get_logger("goal_agent")


def handle(input_json: Dict[str, Any]) -> Dict[str, Any]:
    action = input_json.get("action")
    if not action:
        raise ValueError("action is required in input JSON")

    action = action.upper()
    logger.info("Handling action=%s for user=%s", action, input_json.get("user_id"))

    if action == "DISCOVER_GOALS":
        return discover.run(input_json)
    elif action == "EVALUATE_GOAL":
        return evaluate.run(input_json)
    elif action == "ADJUST_GOALS":
        return adjust.run(input_json)
    elif action == "TRACK_GOAL":
        return track.run(input_json)
    elif action == "BUILD_GOAL_CONTEXT":
        return build_goal_context.run(input_json)
    else:
        raise ValueError(f"Unknown action: {action}")
