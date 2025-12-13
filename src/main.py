from fastapi import FastAPI, Header, HTTPException
from typing import Optional
import httpx
from datetime import datetime, timezone
from src.models.schemas import (
    AgentInput, 
    AgentOutput, 
    FinancialContext,
    TransactionInput,
    GoalInput
)
from src.agents.financial_analyzer import FinancialAnalyzer
from src.agents.goal_analyzer import GoalAnalyzer
from src.agents.budget_advisor import BudgetAdvisor
from src.memory.manager import MemoryManager
from src.config import settings
# Crear tablas al inicio
from src.memory.database import create_tables
create_tables()

app = FastAPI(
    title="FinZen AI Service",
    description="Servicio de IA para análisis financiero y recomendaciones",
    version="1.0.0"
)

memory_manager = MemoryManager()
financial_analyzer = FinancialAnalyzer()
goal_analyzer = GoalAnalyzer()
budget_advisor = BudgetAdvisor()
from fastapi import Body
from pydantic import BaseModel

# Modelos para endpoints de presupuesto
class BudgetSuggestInput(BaseModel):
    user_id: str
    category_id: int
    category_name: str
    start_date: str
    end_date: str
    transactions: Optional[list] = None
    financial_context: Optional[dict] = None
    semantic_profile: Optional[dict] = None

class BudgetReviewInput(BaseModel):
    user_id: str
    budget: dict
    transactions: Optional[list] = None
    financial_context: Optional[dict] = None
    semantic_profile: Optional[dict] = None

@app.post("/budget/suggest")
async def suggest_budget(input_data: BudgetSuggestInput, authorization: Optional[str] = Header(None)):
    """
    Sugiere un presupuesto para una nueva categoría.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    # Obtener datos si faltan
    if not input_data.transactions:
        input_data.transactions = [t.model_dump() for t in await fetch_transactions(authorization)]
    if not input_data.financial_context:
        summary = await fetch_financial_summary(authorization)
        income = float(summary.get("totalIncome", 0) or 0)
        expense = float(summary.get("totalExpense", 0) or 0)
        input_data.financial_context = {
            "monthly_income": income,
            "fixed_expenses": 0,
            "variable_expenses": expense,
            "savings": 0,
            "month_surplus": income - expense
        }
    if not input_data.semantic_profile:
        input_data.semantic_profile = memory_manager.get_semantic_profile(input_data.user_id)
    # Llamar agente
    result = await budget_advisor.suggest_budget(
        category_id=input_data.category_id,
        category_name=input_data.category_name,
        transactions=input_data.transactions,
        financial_context=input_data.financial_context,
        semantic_profile=input_data.semantic_profile,
        start_date=input_data.start_date,
        end_date=input_data.end_date
    )
    return result

@app.post("/budget/review")
async def review_budget(input_data: BudgetReviewInput, authorization: Optional[str] = Header(None)):
    """
    Revisa el cumplimiento de un presupuesto existente.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    if not input_data.transactions:
        input_data.transactions = [t.model_dump() for t in await fetch_transactions(authorization)]
    if not input_data.financial_context:
        summary = await fetch_financial_summary(authorization)
        income = float(summary.get("totalIncome", 0) or 0)
        expense = float(summary.get("totalExpense", 0) or 0)
        input_data.financial_context = {
            "monthly_income": income,
            "fixed_expenses": 0,
            "variable_expenses": expense,
            "savings": 0,
            "month_surplus": income - expense
        }
    if not input_data.semantic_profile:
        input_data.semantic_profile = memory_manager.get_semantic_profile(input_data.user_id)
    result = await budget_advisor.review_budget(
        budget=input_data.budget,
        transactions=input_data.transactions,
        financial_context=input_data.financial_context,
        semantic_profile=input_data.semantic_profile
    )
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "FinZen AI Service",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

async def fetch_transactions(token: str):
    """Obtiene transacciones del microservicio de Transactions con token propagation"""
    try:
        url = f"{settings.TRANSACTIONS_SERVICE_URL}/transactions"
        print(f" Fetching transactions from: {url}")
        print(f" Using token: {token[:50]}...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": token}
            )
            
            print(f" Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f" Fetched {len(data)} transactions")
                
                # Convertir a formato esperado
                transactions = [
                    TransactionInput(
                        id=t.get("id"),
                        amount=float(t.get("amount", 0)),
                        description=t.get("description", ""),
                        date=t.get("date", ""),
                        type=t.get("type", "EXPENSE"),
                        category_id=t.get("categoryId", 0)
                    )
                    for t in data
                ]
                return transactions
            else:
                print(f" Error response: {response.text}")
                return []
    except Exception as e:
        print(f" Error fetching transactions: {e}")
        import traceback
        traceback.print_exc()
        return []

async def fetch_financial_summary(token: str):
    """Obtiene resumen financiero del microservicio de Transactions con token propagation"""
    try:
        url = f"{settings.TRANSACTIONS_SERVICE_URL}/transactions/reports"
        print(f" Fetching reports from: {url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": token}
            )
            
            print(f" Reports response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f" Fetched reports: {data}")
                return data
            else:
                print(f" Error response: {response.text}")
                return {}
    except Exception as e:
        print(f" Error fetching financial summary: {e}")
        return {}

async def fetch_goals(token: str):
    """Obtiene metas del microservicio de Goals con token propagation"""
    try:
        url = f"{settings.GOALS_SERVICE_URL}/goals"
        print(f" Fetching goals from: {url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": token}
            )
            
            print(f" Goals response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f" Fetched {len(data)} goals")
                
                goals = [
                    GoalInput(
                        id=g.get("id"),
                        name=g.get("name", ""),
                        target_amount=float(g.get("targetAmount", 0)),
                        saved_amount=float(g.get("savedAmount", 0)),
                        category=g.get("category", "OTHER"),
                        due_date=g.get("dueDate"),
                        status=g.get("status", "ACTIVE")
                    )
                    for g in data
                ]
                return goals
            else:
                print(f" Error response: {response.text}")
                return []
    except Exception as e:
        print(f" Error fetching goals: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.post("/analyze", response_model=AgentOutput)
async def analyze(input_data: AgentInput,authorization: Optional[str] = Header(None)):
    """
    Endpoint principal de análisis financiero con IA.
    Propaga el token JWT a los microservicios para obtener datos
    y genera recomendaciones personalizadas.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        # 1. Enriquecer datos desde microservicios (API Composition + Token Propagation)
        print(f" Fetching data for user {input_data.user_id}")
        print(f" Authorization header: {authorization[:50]}...")
        
        if not input_data.transactions:
            input_data.transactions = await fetch_transactions(authorization)
            print(f" Loaded {len(input_data.transactions)} transactions")
        
        if not input_data.goals:
            input_data.goals = await fetch_goals(authorization)
            print(f" Loaded {len(input_data.goals)} goals")
        
        if not input_data.financial_context:
            summary = await fetch_financial_summary(authorization)
            income = float(summary.get("totalIncome", 0) or 0)
            expense = float(summary.get("totalExpense", 0) or 0)
            print(f" Financial summary - Income: {income}, Expense: {expense}")
            input_data.financial_context = FinancialContext(
                monthly_income=income,
                fixed_expenses=0,
                variable_expenses=expense,
                savings=0,
                month_surplus=income - expense
            )
        
        # 2. Obtener memoria semántica del usuario
        semantic_profile = memory_manager.get_semantic_profile(input_data.user_id)
        
        # 3. Determinar tipo de análisis según query
        query = (input_data.user_query or "").lower()
        
        if any(word in query for word in ["meta", "objetivo", "ahorro", "viaje", "casa"]):
            # Análisis de metas
            print(" Running Goal Analysis")
            result = await goal_analyzer.analyze(
                query=query,
                goals=[g.model_dump() for g in input_data.goals],
                financial_context=input_data.financial_context.model_dump(),
                semantic_profile=semantic_profile
            )
            analysis_type = "goal_analysis"
        else:
            # Análisis financiero
            print(" Running Financial Analysis")
            result = await financial_analyzer.analyze(
                query=query,
                transactions=[t.model_dump() for t in input_data.transactions],
                financial_context=input_data.financial_context.model_dump(),
                semantic_profile=semantic_profile
            )
            analysis_type = "financial_analysis"
        
        # 4. Guardar interacción en memoria episódica
        memory_manager.log_interaction(
            user_id=input_data.user_id,
            query=input_data.user_query or "análisis general",
            agent_type=analysis_type,
            response=result
        )
        
        # 5. Actualizar memoria semántica cada 5 interacciones
        memory_manager.update_semantic_profile_if_needed(input_data.user_id)
        
        # 6. Formatear respuesta
        return AgentOutput(
            action="ANALYSIS_COMPLETED",
            message=result.get("message", "Análisis completado"),
            data=result
        )
        
    except Exception as e:
        print(f" Error in analysis: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing analysis: {str(e)}"
        )

@app.post("/chat")
async def chat(input_data: AgentInput,authorization: Optional[str] = Header(None)):
    """
    Endpoint para chat conversacional con la IA.
    Mantiene contexto de conversación usando memoria episódica.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Obtener historial reciente
    recent_history = memory_manager.get_recent_interactions(
        input_data.user_id,
        limit=5
    )
    
    # Implementación básica de chat con contexto
    context_messages = "\n".join([
        f"Usuario: {h['query']}\nAsistente: {h['response'].get('message', '')}"
        for h in recent_history
    ])
    
    return {
        "response": f"Chat endpoint activo. Contexto: {len(recent_history)} mensajes anteriores.",
        "history": recent_history,
        "context": context_messages
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)