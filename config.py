import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # URLs internas de tus microservicios (en Azure usarás las URLs reales)
    TRANSACTIONS_SERVICE_URL = os.getenv("TRANSACTIONS_SERVICE_URL", "http://localhost:8082/api")
    GOALS_SERVICE_URL = os.getenv("GOALS_SERVICE_URL", "http://localhost:8083/api")

settings = Settings()