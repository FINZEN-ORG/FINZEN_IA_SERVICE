"""Minimal CrewAI-compatible initializer.

This file exposes a simple `create_agent()` that returns the handle function for the orchestrator.
If you have CrewAI installed, you can replace or extend this module to register tasks/tools using that SDK.
"""
from .agent import handle


def create_agent():
    """Return a callable that the orchestrator can use to dispatch JSON payloads."""
    return handle
