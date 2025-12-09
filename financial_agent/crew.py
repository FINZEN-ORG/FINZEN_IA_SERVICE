# Placeholder for CrewAI-specific helpers; currently uses openai_wrapper

from .openai_wrapper import call_chat


def crew_call(prompt: str, system_message: str = None):
    return call_chat(prompt, system_message=system_message)
