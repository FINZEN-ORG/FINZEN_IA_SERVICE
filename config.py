import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    # Base de Datos de IA (Episodic/Semantic) en tu Postgres Azure
    DATABASE_URL: str
    # URLs de tus microservicios internos
    TRANSACTIONS_SERVICE_URL: str = "http://finzen-api-transactions"
    GOALS_SERVICE_URL: str = "http://finzen-api-goals"

    # URLs internas de tus microservicios (para pruebas locales)
    #OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    #TRANSACTIONS_SERVICE_URL = os.getenv("TRANSACTIONS_SERVICE_URL", "http://localhost:8082/api")
    #GOALS_SERVICE_URL = os.getenv("GOALS_SERVICE_URL", "http://localhost:8083/api")

    class Config:
        env_file = ".env"

settings = Settings()