"""ATR calculation and classification."""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dateutil import parser


def safe_float(x) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def compute_atr(goal: Dict[str, Any], now: Optional[datetime] = None) -> Dict[str, Any]:
    if now is None:
        now = datetime.now(timezone.utc)
    saved = safe_float(goal.get("saved_amount", 0))
    target = safe_float(goal.get("target_amount", 0))
    if target <= 0:
        progress_ratio = 0.0
    else:
        progress_ratio = saved / target

    created = goal.get("created_at")
    due = goal.get("due_date")
    try:
        created_dt = parser.isoparse(created) if created else None
        due_dt = parser.isoparse(due) if due else None
    except Exception:
        created_dt = None
        due_dt = None

    if not created_dt or not due_dt or created_dt >= due_dt:
        time_ratio = 1.0
    else:
        # Handle naive vs aware datetimes safely
        try:
            if (created_dt.tzinfo is None) and (due_dt.tzinfo is None):
                # use naive now for comparison
                now_naive = datetime.utcnow()
                total_time = (due_dt.replace(tzinfo=None) - created_dt.replace(tzinfo=None)).total_seconds()
                elapsed_time = (now_naive - created_dt.replace(tzinfo=None)).total_seconds()
            else:
                # ensure timezone-aware comparisons in UTC
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                else:
                    created_dt = created_dt.astimezone(timezone.utc)
                if due_dt.tzinfo is None:
                    due_dt = due_dt.replace(tzinfo=timezone.utc)
                else:
                    due_dt = due_dt.astimezone(timezone.utc)
                now_aware = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
                total_time = (due_dt - created_dt).total_seconds()
                elapsed_time = (now_aware - created_dt).total_seconds()
        except Exception:
            total_time = 1.0
            elapsed_time = 1.0
        if total_time <= 0:
            time_ratio = 1.0
        else:
            time_ratio = max(0.0001, elapsed_time / total_time)

    atr = (progress_ratio / time_ratio) if time_ratio > 0 else 0.0

    # classification
    if atr > 1.1:
        cls = "adelantada"
    elif 0.9 <= atr <= 1.1:
        cls = "equilibrada"
    elif 0.7 <= atr < 0.9:
        cls = "ligeramente_atrasada"
    elif 0.5 <= atr < 0.7:
        cls = "atrasada"
    else:
        cls = "muy_atrasada"

    return {
        "goal_id": int(goal.get("id")) if goal.get("id") is not None else None,
        "atr": atr,
        "progress_ratio": progress_ratio,
        "time_ratio": time_ratio,
        "classification": cls,
    }
