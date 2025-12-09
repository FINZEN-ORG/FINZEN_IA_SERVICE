"""Database driver for episodic memory for Financial Insight Agent."""
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Text, TIMESTAMP, cast
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import select
from sqlalchemy import String as SAString
from sqlalchemy.exc import SQLAlchemyError
import os
from typing import Any, Dict, Optional, List
from .utils.logging import get_logger
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = get_logger("financial_db")

EPISODIC_DB_HOST = os.environ.get("EPISODIC_DB_HOST")
EPISODIC_DB_PORT = os.environ.get("EPISODIC_DB_PORT")
EPISODIC_DB_NAME = os.environ.get("EPISODIC_DB_NAME")
EPISODIC_DB_USER = os.environ.get("EPISODIC_DB_USER")
EPISODIC_DB_PASSWORD = os.environ.get("EPISODIC_DB_PASSWORD")


def _build_url():
    if not all([EPISODIC_DB_HOST, EPISODIC_DB_PORT, EPISODIC_DB_NAME, EPISODIC_DB_USER, EPISODIC_DB_PASSWORD]):
        raise EnvironmentError("Episodic DB environment variables not fully set")
    return (
        f"postgresql+psycopg2://{EPISODIC_DB_USER}:{EPISODIC_DB_PASSWORD}@{EPISODIC_DB_HOST}:{EPISODIC_DB_PORT}/{EPISODIC_DB_NAME}"
    )


engine = create_engine(_build_url(), echo=False, future=True)
metadata = MetaData()

# Table mapping for episodic memory for financial agent
# Adjusted to match existing table columns provided by the orchestrator/database.
episodic_memory_financial = Table(
    "episodic_memory_financial",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String, nullable=False),
    Column("agent_name", String, nullable=True),
    Column("event_type", String, nullable=False),
    Column("input_payload", JSONB, nullable=True),
    Column("semantic_snapshot", JSONB, nullable=True),
    Column("episodic_context", JSONB, nullable=True),
    Column("output_payload", JSONB, nullable=True),
    Column("used_tone", String, nullable=True),
)


def insert_episodic_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new episodic record and return inserted record metadata.

    record must contain keys matching the table columns above.
    Only keys present in the table mapping will be inserted.
    """
    try:
        with engine.begin() as conn:
            # If DB defines user_id as integer and provided user_id is non-numeric,
            # avoid inserting it directly (would trigger a type error). Instead
            # keep the original external id inside the input_payload for traceability.
            rec = dict(record)
            try:
                user_col = episodic_memory_financial.c.user_id
                # detect if the user_id column is an integer type
                is_user_int = isinstance(user_col.type, Integer)
            except Exception:
                is_user_int = False

            if "user_id" in rec and is_user_int:
                uid = rec.get("user_id")
                # determine if uid is numeric
                numeric = False
                try:
                    if isinstance(uid, int):
                        numeric = True
                    elif isinstance(uid, str) and uid.isdigit():
                        rec["user_id"] = int(uid)
                        numeric = True
                except Exception:
                    numeric = False

                if not numeric:
                    # move to input_payload.external_user_id
                    ip = rec.get("input_payload") or {}
                    ip = dict(ip)
                    ip["external_user_id"] = uid
                    rec["input_payload"] = ip
                    rec.pop("user_id", None)

            # Filter record to available columns to avoid DB errors
            allowed = {c.name for c in episodic_memory_financial.columns}
            filtered = {k: v for k, v in rec.items() if k in allowed}
            ins = episodic_memory_financial.insert().values(**filtered)
            res = conn.execute(ins)
            return {"inserted_id": res.inserted_primary_key[0] if res.inserted_primary_key else None}
    except SQLAlchemyError as e:
        logger.exception("Failed to insert episodic record")
        raise


def query_episodic_by_user(user_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    try:
        # Build a WHERE clause that is safe if DB user_id is numeric but provided user_id is text.
        param_user = user_id
        try:
            user_col = episodic_memory_financial.c.user_id
            is_user_int = isinstance(user_col.type, Integer)
        except Exception:
            is_user_int = False

        with engine.connect() as conn:
            # Order by id desc because some schemas may not have created_at
            if is_user_int and isinstance(user_id, str) and not user_id.isdigit():
                # cast user_id column to text for comparison to avoid bigint text errors
                where_clause = cast(episodic_memory_financial.c.user_id, SAString) == str(user_id)
            else:
                # normal equality (coercion to int if string of digits will work)
                where_clause = episodic_memory_financial.c.user_id == (int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id)

            stmt = select(episodic_memory_financial).where(where_clause).order_by(episodic_memory_financial.c.id.desc()).limit(limit)
            result = conn.execute(stmt)
            rows = [dict(r._mapping) for r in result]
            return rows
    except Exception as e:
        logger.exception("Failed to query episodic memory")
        return []
