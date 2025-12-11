from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import json
from src.memory.database import SessionLocal
from src.memory.models import EpisodicMemory, SemanticProfile
from src.config import settings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

class MemoryManager:
    """
    Gestor centralizado de memoria episódica y semántica.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.1
        )
    
    def log_interaction(self,user_id: int,query: str,agent_type: str,response: Dict) -> None:
        """Guarda una interacción en memoria episódica"""
        db = SessionLocal()
        try:
            memory = EpisodicMemory(
                user_id=user_id,
                query=query,
                agent_used=agent_type,
                response=response,
                created_at=datetime.now(timezone.utc)
            )
            db.add(memory)
            db.commit()
            print(f" Logged interaction for user {user_id}")
        except Exception as e:
            print(f" Error logging interaction: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_recent_interactions(self,user_id: int,limit: int = 10) -> List[Dict]:
        """Obtiene las últimas interacciones del usuario"""
        db = SessionLocal()
        try:
            interactions = db.query(EpisodicMemory)\
                .filter(EpisodicMemory.user_id == user_id)\
                .order_by(desc(EpisodicMemory.created_at))\
                .limit(limit)\
                .all()
            
            return [
                {
                    "query": i.query,
                    "agent": i.agent_used,
                    "response": i.response,
                    "timestamp": i.created_at.isoformat()
                }
                for i in interactions
            ]
        finally:
            db.close()
    
    def get_interaction_count(self, user_id: int) -> int:
        """Cuenta las interacciones del usuario"""
        db = SessionLocal()
        try:
            return db.query(func.count(EpisodicMemory.id))\
                .filter(EpisodicMemory.user_id == user_id)\
                .scalar()
        finally:
            db.close()
    
    def get_semantic_profile(self, user_id: int) -> Dict:
        """Obtiene el perfil semántico del usuario"""
        db = SessionLocal()
        try:
            profile = db.query(SemanticProfile)\
                .filter(SemanticProfile.user_id == user_id)\
                .first()
            
            if profile:
                return profile.attributes or {}
            
            # Perfil por defecto para nuevos usuarios
            return {
                "risk_tolerance": "medium",
                "motivation_style": "balanced",
                "financial_literacy": "beginner",
                "preferred_tone": "friendly"
            }
        finally:
            db.close()
    
    def update_semantic_profile_if_needed(self, user_id: int) -> None:
        """
        Actualiza el perfil semántico si se alcanzó el threshold de interacciones.
        Usa el user_id para filtrar interacciones específicas del usuario.
        """
        db = SessionLocal()
        try:
            profile = db.query(SemanticProfile)\
                .filter(SemanticProfile.user_id == user_id)\
                .first()
            
            # Verificar si necesita actualización
            if profile and profile.last_updated:
                interactions_since = db.query(func.count(EpisodicMemory.id))\
                    .filter(
                        EpisodicMemory.user_id == user_id,
                        EpisodicMemory.created_at > profile.last_updated
                    ).scalar()
                
                if interactions_since < settings.SEMANTIC_UPDATE_THRESHOLD:
                    return
            
            # Obtener interacciones recientes del usuario específico
            recent = self.get_recent_interactions(
                user_id,
                limit=settings.SEMANTIC_UPDATE_THRESHOLD * 2
            )
            
            if not recent:
                return
            
            # Generar nuevo perfil semántico con LLM usando las interacciones del usuario
            new_profile = self._generate_semantic_profile(recent)
            
            if not new_profile:
                return
            
            # Actualizar o crear perfil
            if profile:
                current_attrs = profile.attributes or {}
                current_attrs.update(new_profile)
                profile.attributes = current_attrs
                profile.last_updated = datetime.now(timezone.utc)
            else:
                profile = SemanticProfile(
                    user_id=user_id,
                    attributes=new_profile,
                    last_updated=datetime.now(timezone.utc)
                )
                db.add(profile)
            
            db.commit()
            print(f" Updated semantic profile for user {user_id}")
            
        except Exception as e:
            print(f" Error updating semantic profile: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _generate_semantic_profile(self,interactions: List[Dict]) -> Optional[Dict]:
        """
        Usa el LLM para generar un perfil semántico compacto
        basado en las interacciones recientes del usuario.
        """
        try:
            prompt = ChatPromptTemplate.from_template("""
                Eres un experto en análisis de comportamiento financiero.

                Analiza las siguientes interacciones del usuario y genera un perfil semántico compacto.

                INTERACCIONES:
                {interactions}

                Genera un perfil que incluya:
                - risk_tolerance: low, medium, high
                - motivation_style: goal_oriented, balance_focused, stress_averse
                - financial_literacy: beginner, intermediate, advanced
                - spending_patterns: [lista de patrones detectados]
                - preferred_categories: [categorías donde más gasta]
                - emotional_state: positive, neutral, concerned, stressed
                - preferred_tone: friendly, formal, encouraging, direct

                RESPONDE SOLO EN JSON:
            """)
            chain = prompt | self.llm | JsonOutputParser()
            interactions_text = json.dumps(interactions, indent=2, ensure_ascii=False)
            result = chain.invoke({"interactions": interactions_text})
            return result
        except Exception as e:
            print(f" Error generating semantic profile: {e}")
            return None
    
    def cleanup_old_interactions(self, days: int = None) -> int:
        """
        Elimina interacciones episódicas antiguas para mantener la BD limpia
        """
        if days is None:
            days = settings.EPISODIC_RETENTION_DAYS
        db = SessionLocal()
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            deleted = db.query(EpisodicMemory)\
                .filter(EpisodicMemory.created_at < cutoff_date)\
                .delete()
            db.commit()
            print(f" Cleaned up {deleted} old interactions")
            return deleted
        except Exception as e:
            print(f" Error cleaning up interactions: {e}")
            db.rollback()
            return 0
        finally:
            db.close()