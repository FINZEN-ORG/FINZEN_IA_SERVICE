from pydantic import BaseModel
from typing import List, Optional, Any, Dict, Union

# --- Modelos de Entrada (Lo que recibe la API) ---

class TransactionInput(BaseModel):
    id: str | int
    amount: float
    description: str
    date: str
    category_id: int | str
    type: str  # "INCOME" | "EXPENSE"

class FinancialContext(BaseModel):
    monthly_income: float
    fixed_expenses: float
    variable_expenses: float
    savings: float
    month_surplus: float

class GoalInput(BaseModel):
    id: Optional[int] = None
    name: str
    target_amount: float
    saved_amount: float
    category: str
    due_date: Optional[str] = None

class AgentInput(BaseModel):
    user_id: int
    user_query: Optional[str] = None
    context: str = "friendly"  # Tono
    
    # Datos inyectados por el orquestador (no por el usuario)
    transactions: List[TransactionInput] = []
    goals: List[GoalInput] = []
    financial_context: Optional[FinancialContext] = None
    semantic_memory: Dict[str, Any] = {}

# --- Modelos de Salida (Lo que devuelve la IA) ---

class AIRecommendation(BaseModel):
    message: str
    sentiment: str  # POSITIVE, WARNING, CRITICAL, INFO
    actionable_tip: Optional[str] = None
    data: Optional[Dict[str, Any]] = None # Datos extra (ej: lista de hormiga)