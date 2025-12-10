from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime
from src.memory.database import Base, SessionLocal

class EpisodicMemory(Base):
    __tablename__ = "episodic_memory"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    query = Column(String)
    agent_used = Column(String)
    response = Column(JSON) # Aquí guardamos el JSON complejo de respuesta
    created_at = Column(DateTime, default=datetime.utcnow)

def log_interaction(user_id, query, agent, response):
    db = SessionLocal()
    try:
        mem = EpisodicMemory(user_id=user_id, query=query, agent_used=agent, response=response)
        db.add(mem)
        db.commit()
    finally:
        db.close()