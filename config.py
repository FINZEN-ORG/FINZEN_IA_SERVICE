import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Conexión a la BD de IA (finzen_ai_db)
    DATABASE_URL: str
    
    # URLs de tus otros microservicios
    # En local usa http://host.docker.internal:808X
    # En Azure usa las URLs https://...
    TRANSACTIONS_SERVICE_URL: str
    GOALS_SERVICE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()