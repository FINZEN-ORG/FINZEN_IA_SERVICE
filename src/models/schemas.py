from pydantic import BaseModel
from typing import List, Optional, Any, Dict

# --- INPUTS ---
class TransactionInput(BaseModel):
    id: int | str
    amount: float
    description: str
    date: str
    type: str
    category_id: int | str

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
    fixed_expenses: float
    variable_expenses: float
    savings: float
    month_surplus: float

class AgentInput(BaseModel):
    user_id: int
    user_query: Optional[str] = None
    context: str = "friendly"
    transactions: List[TransactionInput] = []
    goals: List[GoalInput] = []
    financial_context: Optional[FinancialContext] = None
    semantic_memory: Dict[str, Any] = {}

# --- OUTPUTS ---
class AgentOutput(BaseModel):
    action: str
    message: str
    data: Dict[str, Any]

class AIRecommendation(BaseModel):
    message: str
    sentiment: str
    actionable_tip: Optional[str] = None
    data: Optional[Dict[str, Any]] = None