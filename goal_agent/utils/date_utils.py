"""Utilities for date calculations and formatting."""
from datetime import datetime, timezone
from dateutil import parser
from typing import Optional


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(d: Optional[str]) -> Optional[datetime]:
    if d is None:
        return None
    try:
        return parser.isoparse(d)
    except Exception:
        try:
            return datetime.fromisoformat(d)
        except Exception:
            return None


def isoformat(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()
