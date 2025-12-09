# src/memory/episodic.py
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from src.config import settings

Base = declarative_base()

class EpisodicMemory(Base):
    __tablename__ = "episodic_memory"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    query = Column(String)
    response = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def log_interaction(user_id, query, response):
    db = SessionLocal()
    try:
        mem = EpisodicMemory(user_id=user_id, query=query, response=response)
        db.add(mem)
        db.commit()
    finally:
        db.close()