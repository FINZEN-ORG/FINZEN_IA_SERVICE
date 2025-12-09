from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union

class Transaction(BaseModel):
    id: str
    amount: float
    category_id: Optional[str]
    description: Optional[str]
    date: str
    type: str

class FinancialContext(BaseModel):
    monthly_income: float
    fixed_expenses: float
    variable_expenses: float
    savings: float
    month_surplus: float

class OrchestratorInput(BaseModel):
    mode: str
    event_type: str
    user_id: Union[str, int]
    semantic_memory: Optional[dict]
    financial_context: FinancialContext
    transactions: List[Transaction]
    goals: Optional[List[Any]]

class AgentOutput(BaseModel):
    status: str
    mode: str
    insights: dict
    episodic_record_created: bool
