# src/memory/episodic.py
from sqlalchemy import Column, Integer, String, JSON, DateTime
from src.database import Base
from datetime import datetime

class EpisodicMemory(Base):
    __tablename__ = "episodic_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    agent_name = Column(String)
    event_type = Column(String)
    input_payload = Column(JSON) # Aquí guardamos el JSON complejo que ella diseñó
    output_response = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Función para guardar (reemplaza al insert de ella)
def log_interaction(db, user_id, agent, event_type, input_data, output):
    memory = EpisodicMemory(
        user_id=user_id,
        agent_name=agent,
        event_type=event_type,
        input_payload=input_data,
        output_response=output
    )
    db.add(memory)
    db.commit()