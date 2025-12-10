from pydantic import BaseModel
from typing import List, Optional, Any, Dict

# --- Modelos de Entrada (Lo que recibe la API) ---

class TransactionInput(BaseModel):
    id: str | int
    amount: float
    description: str
    date: str
    category_id: int | str
    type: str  # "INCOME" | "EXPENSE"

class GoalInput(BaseModel):
    id: int
    name: str
    target_amount: float
    saved_amount: float
    category: str
    due_date: Optional[str] = None
    status: str

class FinancialContext(BaseModel):
    monthly_income: float
    monthly_expenses: float
    month_surplus: float
    savings: float

class AgentInput(BaseModel):
    user_id: int
    user_query: Optional[str] = None
    context: str = "friendly"  # Tono
    # Datos inyectados por el orquestador (no por el usuario)
    # Datos opcionales (si el frontend ya los tiene)
    transactions: List[TransactionInput] = []
    goals: List[GoalInput] = []
    financial_context: Optional[FinancialContext] = None
    semantic_memory: Dict[str, Any] = {}

# --- Modelos de Salida (Lo que devuelve la IA) ---
class AIRecommendation(BaseModel):
    action: str
    message: str
    data: Dict[str, Any] # Aquí va el JSON detallado que generan los prompts complejos