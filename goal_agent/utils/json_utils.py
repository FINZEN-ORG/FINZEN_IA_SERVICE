"""Helpers to robustly parse JSON-like text returned by LLMs.

This module tries multiple strategies to extract JSON from free text:
- direct json.loads
- extract first {...} or [...] block with regex
- replace single quotes -> double quotes and try again
- use ast.literal_eval as last resort
"""
import json
import re
import ast
from typing import Any, Optional
from .logging import get_logger

logger = get_logger("json_utils")


def _find_json_like(text: str) -> Optional[str]:
    # find the first JSON object or array in the text
    patterns = [r"\{.*\}", r"\[.*\]"]
    for p in patterns:
        m = re.search(p, text, re.DOTALL)
        if m:
            return m.group(0)
    return None


def safe_parse_json(text: str) -> Optional[Any]:
    if not text:
        return None

    # 1. try direct
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. try to extract json-like block
    try:
        block = _find_json_like(text)
        if block:
            try:
                return json.loads(block)
            except Exception:
                # try repair single quotes
                repaired = block.replace("'", '"')
                repaired = re.sub(r",\s*}\s*$", "}", repaired)
                try:
                    return json.loads(repaired)
                except Exception:
                    pass
    except Exception:
        pass

    # 3. try ast.literal_eval (can handle Python dicts with single quotes)
    try:
        val = ast.literal_eval(text)
        return val
    except Exception:
        pass

    # 4. last attempt: extract block and ast.literal_eval
    try:
        block = _find_json_like(text)
        if block:
            try:
                return ast.literal_eval(block)
            except Exception:
                pass
    except Exception:
        pass

    logger.debug("safe_parse_json: unable to parse text as JSON")
    return None
