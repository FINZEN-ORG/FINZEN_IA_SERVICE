import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.3
    DATABASE_URL: str  # Base de datos PostgreSQL (finzen_ai_db)
    # URLs de microservicios
    # En local usa http://host.docker.internal:808X
    # En Azure usa las URLs https://...
    TRANSACTIONS_SERVICE_URL: str
    GOALS_SERVICE_URL: str
    # Configuración de memoria
    SEMANTIC_UPDATE_THRESHOLD: int = 5  # Actualizar cada 5 interacciones
    EPISODIC_RETENTION_DAYS: int = 60   # Mantener historial 60 días
    # Configuración de análisis
    MAX_TRANSACTIONS_FOR_ANALYSIS: int = 100
    ANT_EXPENSE_THRESHOLD: float = 5000.0  # COP - gastos hormiga
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()