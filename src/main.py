from fastapi import FastAPI, HTTPException
from src.models.schemas import AgentInput, AIRecommendation, AgentOutput, FinancialContext
from src.services.transaction_service import get_user_transactions, get_financial_summary
from src.services.goal_service import get_user_goals
from src.orchestration.graph import app as graph_app

app = FastAPI(title="FinZen AI Service")

@app.post("/analyze", response_model=AIRecommendation)
async def analyze(input_data: AgentInput):
    # 1. Enriquecer datos (API Composition)
    # Si el frontend no mandó las transacciones, las pedimos nosotros a los microservicios
    transactions = input_data.transactions
    if not transactions:
        input_data.transactions = await get_user_transactions(input_data.user_id)
    
    goals = input_data.goals
    if not goals:
        input_data.goals = await get_user_goals(input_data.user_id)
        
    financial_context = input_data.financial_context
    if not financial_context:
        # Calcular contexto básico si no viene
        summary = await get_financial_summary(input_data.user_id)
        financial_context = FinancialContext(
            monthly_income=summary.get("totalIncome", 0),
            fixed_expenses=0, # Simplificación
            variable_expenses=summary.get("totalExpense", 0),
            savings=0,
            month_surplus=summary.get("totalIncome", 0) - summary.get("totalExpense", 0)
        )

    # 2. Ejecutar Grafo
    initial_state = {
        "user_id": input_data.user_id,
        "user_query": input_data.user_query or "analisis general",
        "transactions": [t.dict() for t in transactions] if transactions else [],
        "goals": [g.dict() for g in goals] if goals else [],
        "financial_context": financial_context.dict() if input_data.financial_context else {}
    }

    result = await graph_app.ainvoke(initial_state)

    # 3. Formatear Respuesta
    response_data = result.get("financial_analysis") or result.get("goal_analysis") or {}
    
    return AgentOutput(
        action="ANALYSIS_COMPLETED",
        message=result.get("final_response", "Análisis completado"),
        data=response_data
    )