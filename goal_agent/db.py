"""Database driver for episodic memory using SQLAlchemy."""
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import select
from sqlalchemy.exc import SQLAlchemyError
import os
from typing import Any, Dict, Optional, List
from .utils.logging import get_logger
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = get_logger("db")

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

# Table mapping for episodic memory (reflecting the screenshot)
episodic_memory_goals = Table(
    "episodic_memory_goals",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String, nullable=False),
    Column("goal_name", String, nullable=True),
    Column("event_type", String, nullable=False),
    Column("message", Text, nullable=True),
    Column("parameters", JSONB, nullable=True),
    Column("created_at", TIMESTAMP, nullable=False),
)


def insert_episodic_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new episodic record and return inserted record metadata.

    record must match keys: user_id, goal_name, event_type, message, parameters, created_at
    """
    try:
        with engine.begin() as conn:
            ins = episodic_memory_goals.insert().values(**record)
            res = conn.execute(ins)
            return {"inserted_id": res.inserted_primary_key[0] if res.inserted_primary_key else None}
    except SQLAlchemyError as e:
        logger.exception("Failed to insert episodic record")
        raise


def query_episodic_by_user(user_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    try:
        with engine.connect() as conn:
            stmt = select(episdodic_select := episodic_memory_goals).where(episdodic_select.c.user_id == user_id).order_by(episdodic_select.c.created_at.desc()).limit(limit)
            result = conn.execute(stmt)
            rows = [dict(r._mapping) for r in result]
            return rows
    except Exception as e:
        logger.exception("Failed to query episodic memory")
        return []
