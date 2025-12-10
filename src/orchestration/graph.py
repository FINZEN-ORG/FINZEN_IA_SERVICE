# src/orchestration/graph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
from src.agents import financial_agent, goal_agent

# Estado compartido entre agentes (el "sobre" que se pasan)
class AgentState(TypedDict):
    user_id: int
    user_query: str
    transactions: List[dict]
    goals: List[dict]
    financial_context: Dict[str, Any]
    financial_analysis: Dict[str, Any]
    goal_analysis: Dict[str, Any]
    final_response: str

# El Router decide a quién llamar basado en la pregunta
def router(state: AgentState):
    q = state["user_query"].lower()
    if "meta" in q or "ahorro" in q or "viaje" in q or "objetivo" in q:
        return "goal_agent"
    return "financial_agent"

# Definición del grafo
workflow = StateGraph(AgentState)

workflow.add_node("financial_agent", financial_agent.run)
workflow.add_node("goal_agent", goal_agent.run)

workflow.set_conditional_entry_point(
    router,
    {"financial_agent": "financial_agent", "goal_agent": "goal_agent"}
)

workflow.add_edge("financial_agent", END)
workflow.add_edge("goal_agent", END)

app = workflow.compile()