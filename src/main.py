from fastapi import FastAPI
from src.models.schemas import AgentInput, AgentOutput, FinancialContext
from src.services.transaction_service import get_user_transactions, get_financial_summary
from src.services.goal_service import get_user_goals
from src.orchestration.graph import app as graph_app
from src.memory.database import create_tables
from src.memory.episodic import log_interaction

# Inicializar DB al arrancar
create_tables()

app = FastAPI(title="FinZen AI Service")

@app.post("/analyze", response_model=AgentOutput)
async def analyze(input_data: AgentInput):
    # 1. API Composition (Llenar datos faltantes)
    if not input_data.transactions:
        input_data.transactions = await get_user_transactions(input_data.user_id)
    
    if not input_data.goals:
        input_data.goals = await get_user_goals(input_data.user_id)
        
    if not input_data.financial_context:
        summary = await get_financial_summary(input_data.user_id)
        # Mapeo simple del resumen de transacciones a contexto financiero
        income = summary.get("totalIncome", 0)
        expense = summary.get("totalExpense", 0)
        input_data.financial_context = FinancialContext(
            monthly_income=income,
            monthly_expenses=expense,
            variable_expenses=expense, # Simplificación
            fixed_expenses=0,
            month_surplus=income - expense,
            savings=0
        )

    # 2. Ejecutar Grafo de LangChain
    # Convertimos los modelos Pydantic a dicts para LangGraph
    initial_state = {
        "user_id": input_data.user_id,
        "user_query": input_data.user_query or "analisis general",
        "transactions": input_data.transactions, 
        "goals": input_data.goals,
        "financial_context": input_data.financial_context.dict()
    }

    result = await graph_app.ainvoke(initial_state)

    # 3. Extraer resultados
    # El resultado estará en 'financial_analysis' O 'goal_analysis' dependiendo del agente que corrió
    analysis_data = result.get("financial_analysis") or result.get("goal_analysis") or {}
    message = result.get("final_response", "Proceso completado")

    # 4. Guardar Memoria Episódica
    log_interaction(
        user_id=input_data.user_id,
        query=initial_state["user_query"],
        agent="AI_AGENT", 
        response=analysis_data
    )

    return AgentOutput(
        action="ANALYSIS_COMPLETED",
        message=message,
        data=analysis_data
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)