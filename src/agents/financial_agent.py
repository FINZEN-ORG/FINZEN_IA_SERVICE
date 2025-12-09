import json
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from src.config import settings
from src.agents import prompts

llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL, temperature=0)

async def run(state: dict):
    """
    Analiza la salud financiera o gastos hormiga.
    """
    print("--- Financial Agent Running ---")
    user_query = state.get("user_query", "").lower()
    transactions = state.get("transactions", [])
    financial_ctx = state.get("financial_context", {})
    tone = state.get("context", "friendly")

    # Selección de Prompt basado en intención (Router simple)
    if "hormiga" in user_query or "leaks" in user_query:
        prompt_template = prompts.ANT_EXPENSES_PROMPT
    else:
        prompt_template = prompts.HEALTH_PROMPT

    # Construir cadena
    chain = prompt_template | llm | StrOutputParser()

    # Simplificar transacciones para no gastar tokens
    tx_summary = str([t.dict() for t in transactions[:20]]) 

    try:
        response_str = chain.invoke({
            "tone": tone,
            "income": financial_ctx.monthly_income,
            "expenses": financial_ctx.fixed_expenses + financial_ctx.variable_expenses,
            "surplus": financial_ctx.month_surplus,
            "transactions": tx_summary
        })
        
        # Parsear JSON (OpenAI a veces añade texto extra, LangChain suele limpiarlo pero aseguramos)
        clean_json = response_str.replace("```json", "").replace("```", "")
        return json.loads(clean_json)

    except Exception as e:
        print(f"Error in Financial Agent: {e}")
        return {
            "message": "No pude analizar tus finanzas en este momento.",
            "sentiment": "INFO",
            "actionable_tip": "Intenta más tarde."
        }