import json
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from src.config import settings
from src.agents import prompts

llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL, temperature=0)

def run(state: dict):
    """
    Sugiere o evalúa metas.
    """
    print("--- Goal Agent Running ---")
    user_query = state.get("user_query", "").lower()
    goals = state.get("goals", [])
    financial_ctx = state.get("financial_context", {})
    tone = state.get("context", "friendly")

    # Selección de Lógica
    if "evaluar" in user_query or "puedo" in user_query:
        # Lógica de Evaluación (Extraer la meta del query es complejo sin NLP, asumimos contexto general)
        prompt_template = prompts.EVALUATE_GOAL_PROMPT
        # Aquí deberías extraer qué meta quiere evaluar del string user_query
        new_goal_desc = user_query 
    else:
        # Por defecto sugerir (Discover)
        prompt_template = prompts.DISCOVER_GOALS_PROMPT
        new_goal_desc = ""

    chain = prompt_template | llm | StrOutputParser()

    try:
        response_str = chain.invoke({
            "tone": tone,
            "financial_context": str(financial_ctx.dict()),
            "existing_goals": str([g.dict() for g in goals]),
            "new_goal": new_goal_desc
        })
        
        clean_json = response_str.replace("```json", "").replace("```", "")
        return json.loads(clean_json)

    except Exception as e:
        print(f"Error in Goal Agent: {e}")
        return {
            "message": "No pude procesar tus metas.",
            "sentiment": "INFO",
            "actionable_tip": "Define un monto y fecha."
        }