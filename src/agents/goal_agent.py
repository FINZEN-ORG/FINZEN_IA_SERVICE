import json
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from config import settings
from src.agents import goal_prompts

llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL, temperature=0)

async def run(state: dict):
    print("--- Goal Agent Running ---")
    query = state.get("user_query", "").lower()
    goals = state.get("goals", [])
    financial_ctx = state.get("financial_context", {})
    surplus = financial_ctx.get("month_surplus", 0)

    # 1. Router interno
    if "sugerir" in query or "nueva" in query:
        prompt = goal_prompts.DISCOVER_PROMPT
        inputs = {"surplus": surplus, "existing_goals": str(goals), "financial_context": str(financial_ctx)}
    elif "evaluar" in query:
        prompt = goal_prompts.EVALUATE_PROMPT
        inputs = {"new_goal": query, "surplus": surplus, "existing_goals": str(goals)}
    else:
        # Default: Track/Status
        prompt = goal_prompts.TRACK_PROMPT
        inputs = {"goals": str(goals), "surplus": surplus}

    # 2. Ejecutar
    chain = prompt | llm | StrOutputParser()
    
    try:
        res = await chain.ainvoke({**inputs, "tone": "friendly"})
        clean_json = res.replace("```json", "").replace("```", "")
        data = json.loads(clean_json)
        return {
            "goal_analysis": data,
            "final_response": "Aquí está el análisis de tus metas."
        }
    except Exception as e:
        return {"error": str(e)}