from fastapi import FastAPI
from src.models.schemas import AgentInput, AgentOutput, FinancialContext
from src.services.transaction_service import get_user_transactions, get_financial_summary
from src.services.goal_service import get_user_goals
from src.orchestration.graph import app as graph_app
from src.memory.episodic import create_tables, log_interaction

# Crear tablas al inicio
create_tables()

app = FastAPI(title="FinZen AI Service")

# CORRECCIÓN: response_model ahora es AgentOutput
@app.post("/analyze", response_model=AgentOutput)
async def analyze(input_data: AgentInput):
    # 1. Enriquecer datos (API Composition)
    if not input_data.transactions:
        input_data.transactions = await get_user_transactions(input_data.user_id)
    
    if not input_data.goals:
        input_data.goals = await get_user_goals(input_data.user_id)
        
    if not input_data.financial_context:
        summary = await get_financial_summary(input_data.user_id)
        # Manejo seguro de valores nulos
        income = summary.get("totalIncome", 0) or 0
        expense = summary.get("totalExpense", 0) or 0
        
        input_data.financial_context = FinancialContext(
            monthly_income=float(income),
            fixed_expenses=0,
            variable_expenses=float(expense),
            savings=0,
            month_surplus=float(income - expense)
        )

    # 2. Ejecutar Grafo
    initial_state = {
        "user_id": input_data.user_id,
        "user_query": input_data.user_query or "analisis general",
        # Convertir modelos Pydantic a dicts para LangGraph
        "transactions": [t.model_dump() for t in input_data.transactions],
        "goals": [g.model_dump() for g in input_data.goals],
        "financial_context": input_data.financial_context.model_dump() if input_data.financial_context else {},
        # Inicializar claves opcionales para evitar KeyError en el grafo
        "financial_analysis": {},
        "goal_analysis": {},
        "final_response": ""
    }

    result = await graph_app.ainvoke(initial_state)

    # 3. Formatear Respuesta
    response_data = result.get("financial_analysis") or result.get("goal_analysis") or {}
    message = result.get("final_response") or "Análisis completado"

    # 4. Guardar Memoria
    try:
        log_interaction(
            user_id=input_data.user_id,
            query=initial_state["user_query"],
            response=response_data 
        )
    except Exception as e:
        print(f"Error logging interaction: {e}")

    return AgentOutput(
        action="ANALYSIS_COMPLETED",
        message=message,
        data=response_data
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)