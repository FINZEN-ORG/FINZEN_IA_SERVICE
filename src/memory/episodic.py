from sqlalchemy import Column, Integer, JSON, DateTime, String
from src.memory.database import Base, SessionLocal

class SemanticProfile(Base):
    __tablename__ = "semantic_profile"
    user_id = Column(Integer, primary_key=True) # Un perfil por usuario
    attributes = Column(JSON) # Ej: {"risk_tolerance": "low", "hobbies": ["coffee"]}

def get_profile(user_id):
    db = SessionLocal()
    try:
        return db.query(SemanticProfile).filter_by(user_id=user_id).first()
    finally:
        db.close()

def update_profile(user_id, attributes):
    db = SessionLocal()
    try:
        profile = db.query(SemanticProfile).filter_by(user_id=user_id).first()
        if not profile:
            profile = SemanticProfile(user_id=user_id, attributes=attributes)
            db.add(profile)
        else:
            # Merge simple de diccionarios
            current = dict(profile.attributes or {})
            current.update(attributes)
            profile.attributes = current
        db.commit()
    finally:
        db.close()