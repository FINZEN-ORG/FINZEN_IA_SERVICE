from sqlalchemy import Column, Integer, String, JSON, DateTime, Index
from datetime import datetime
from src.memory.database import Base

class EpisodicMemory(Base):
    """
    Memoria episódica: almacena interacciones cronológicas del usuario.
    Permite rastrear el historial de consultas y respuestas.
    """
    __tablename__ = "episodic_memory"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    query = Column(String, nullable=False)
    agent_used = Column(String, nullable=False)  # 'financial_analysis' o 'goal_analysis'
    response = Column(JSON, nullable=False)  # Respuesta completa del agente
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
    )

class SemanticProfile(Base):
    """
    Memoria semántica: perfil compacto del usuario.
    Se recalcula automáticamente cada X interacciones usando LLM.
    """
    __tablename__ = "semantic_profile"
    user_id = Column(Integer, primary_key=True)
    attributes = Column(JSON, nullable=False, default=dict)
    # Atributos típicos:
    # {
    #   "risk_tolerance": "low|medium|high",
    #   "motivation_style": "goal_oriented|balance_focused|stress_averse",
    #   "financial_literacy": "beginner|intermediate|advanced",
    #   "spending_patterns": ["frequent_food", "weekend_entertainment"],
    #   "preferred_categories": [1, 3, 7],
    #   "emotional_state": "positive|neutral|concerned|stressed",
    #   "preferred_tone": "friendly|formal|encouraging|direct"
    # }
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)