"""OpenAI wrapper for calling LLMs (gpt-4o-mini or configured model).

This module centralizes calls, retries and simple temperature control.
"""
import os
import time
import logging
from tenacity import retry, wait_exponential, stop_after_attempt
import openai
from .utils.logging import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger("openai_wrapper")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

if OPENAI_API_KEY is None:
    logger.warning("OPENAI_API_KEY is not set. Calls may fail until provided in env or .env file.")

# Initialize modern OpenAI client (openai>=1.0.0)
try:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
except Exception:
    client = None


@retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
def call_chat(
    prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 800,
    system_message: str | None = None,
) -> str:
    """Call OpenAI Chat Completions API and return assistant text.

    Accepts an optional `system_message` which will be sent as the system role to
    strongly instruct the model (for example to force JSON-only outputs).
    """
    if client is None:
        logger.error(
            "OpenAI client not initialized. Ensure OPENAI_API_KEY is set and package is compatible."
        )
        raise RuntimeError("OpenAI client not initialized")

    try:
        logger.debug("Calling OpenAI model %s via modern client", MODEL)
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # New client returns choices with message object
        content = ""
        if resp and getattr(resp, "choices", None):
            first = resp.choices[0]
            msg = getattr(first, "message", None) or (first.get("message") if isinstance(first, dict) else None)
            if isinstance(msg, dict):
                content = msg.get("content", "")
            else:
                content = getattr(msg, "content", "")

        text = content.strip() if content else ""
        # Log raw response for debugging (debug level)
        logger.debug("OpenAI raw response: %s", text)
        logger.debug("OpenAI response length=%d", len(text))
        return text
    except Exception:
        logger.exception("OpenAI call failed, will retry if attempts remain")
        raise
