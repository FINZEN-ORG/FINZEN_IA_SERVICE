from fastapi import FastAPI, HTTPException
from src.models.schemas import AgentInput, AIRecommendation, FinancialContext
from src.services.transaction_service import get_user_transactions, get_financial_summary
from src.services.goal_service import get_user_goals
from src.agents import financial_agent, goal_agent

app = FastAPI(title="FinZen AI Service")

@app.post("/analyze", response_model=AIRecommendation)
async def analyze(input_data: AgentInput):
    # 1. Enriquecer datos (API Composition)
    # Si el frontend no mandó las transacciones, las pedimos nosotros a los microservicios
    if not input_data.transactions:
        input_data.transactions = await get_user_transactions(input_data.user_id)
    
    if not input_data.goals:
        input_data.goals = await get_user_goals(input_data.user_id)
        
    if not input_data.financial_context:
        # Calcular contexto básico si no viene
        summary = await get_financial_summary(input_data.user_id)
        input_data.financial_context = FinancialContext(
            monthly_income=summary.get("totalIncome", 0),
            fixed_expenses=0, # Simplificación
            variable_expenses=summary.get("totalExpense", 0),
            savings=0,
            month_surplus=summary.get("totalIncome", 0) - summary.get("totalExpense", 0)
        )

    # 2. Router Lógico (LangGraph simplificado)
    query = (input_data.user_query or "").lower()
    
    if "meta" in query or "ahorro" in query or "viaje" in query or "comprar" in query:
        # Delegar a Agente de Metas
        result = goal_agent.run(input_data.dict())
    else:
        # Delegar a Agente Financiero (Default)
        result = financial_agent.run(input_data.dict())

    # 3. Guardar en Memoria Episódica (PostgreSQL)
    # TODO: Llamar a src/memory/episodic.py para guardar result en DB
    
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)