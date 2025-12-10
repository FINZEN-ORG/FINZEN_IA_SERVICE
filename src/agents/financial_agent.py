import json
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from config import settings
from src.agents import financial_prompts

llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL, temperature=0)

async def run(state: dict):
    print("--- Financial Agent Running ---")
    
    # 1. Extraer contexto
    financial_ctx = state.get("financial_context", {})
    transactions = state.get("transactions", [])
    query = state.get("user_query", "").lower()
    
    # 2. Selección de Prompt
    if "hormiga" in query:
        prompt = financial_prompts.ANT_EXPENSES_PROMPT
    elif "fugas" in query or "leaks" in query:
        prompt = financial_prompts.LEAKS_PROMPT
    else:
        prompt = financial_prompts.HEALTH_PROMPT

    # 3. Ejecutar Cadena
    chain = prompt | llm | StrOutputParser()
    
    # Simplificamos transacciones para el prompt
    # Nota: transactions aquí es una lista de dicts porque ya se convirtió en main.py
    tx_summary = str(transactions[:15])

    try:
        res = await chain.ainvoke({
            "tone": "friendly",
            "income": financial_ctx.get("monthly_income", 0),
            "expenses": financial_ctx.get("monthly_expenses", 0),
            "surplus": financial_ctx.get("month_surplus", 0),
            "transactions": tx_summary
        })
        
        # Limpieza de JSON
        clean_json = res.replace("```json", "").replace("```", "")
        data = json.loads(clean_json)
        
        return {
            "financial_analysis": data,
            "final_response": "He analizado tus finanzas. Revisa el detalle."
        }
    except Exception as e:
        print(f"Error in Financial Agent: {e}")
        return {"error": str(e)}