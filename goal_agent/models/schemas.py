"""Pydantic models for agent input and outputs."""
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class AgentInput(BaseModel):
    action: str
    goals: Optional[List[Dict[str, Any]]] = None
    financial_context: Optional[Dict[str, Any]] = None
    semantic_memory: Optional[Dict[str, Any]] = None
    new_goal_proposal: Optional[Dict[str, Any]] = None
    goal_id: Optional[int] = None
    user_id: str


class SuggestedGoal(BaseModel):
    name: str
    reason: str
    estimated_target: float


class DiscoverOutput(BaseModel):
    suggested_goals: List[SuggestedGoal]


class EvaluateOutput(BaseModel):
    viable: bool
    reason: Optional[str]
    suggested_adjustments: Optional[Dict[str, Any]]


class Adjustment(BaseModel):
    goal_id: int
    allocated_amount: float
    reason: str


class AdjustOutput(BaseModel):
    adjustments: List[Adjustment]
    surplus_used: float
    emotional_message: str


class TrackOutput(BaseModel):
    goal_id: int
    status: str
    message: str
    projections: Dict[str, Any]
