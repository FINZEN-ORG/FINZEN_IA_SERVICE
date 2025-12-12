from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.config import settings
from src.agents.financial_analyzer import FinancialAnalyzer

class BudgetAdvisor:
    """
    Agente especializado en presupuestos.
    Sugiere montos de presupuesto para nuevas categorías y revisa el cumplimiento de presupuestos existentes.
    Usa el análisis financiero del usuario y su perfil para personalizar recomendaciones.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE
        )
        self.financial_analyzer = FinancialAnalyzer()

    async def suggest_budget(self, category_id: int, transactions: List[Dict], financial_context: Dict, semantic_profile: Dict, start_date: str, end_date: str) -> Dict:
        """
        Sugiere un monto de presupuesto para una nueva categoría.
        Devuelve monto sugerido, fechas, explicación y tip.
        """
        # Obtener análisis financiero general
        analysis = await self.financial_analyzer.analyze(
            query="salud financiera",
            transactions=transactions,
            financial_context=financial_context,
            semantic_profile=semantic_profile
        )

        prompt = ChatPromptTemplate.from_template("""
            Eres un asesor experto en presupuestos personales.
            El usuario está creando una nueva categoría de presupuesto.

            DATOS DE LA CATEGORÍA:
            - category_id: {category_id}
            - Fecha inicio: {start_date}
            - Fecha fin: {end_date}

            ANÁLISIS FINANCIERO DEL USUARIO:
            {analysis}

            TRANSACCIONES RELEVANTES:
            {transactions}

            PERFIL DEL USUARIO:
            {profile}

            SUGIERE:
            1. Un monto de presupuesto recomendado para la categoría (basado en hábitos y salud financiera)
            2. Una explicación clara del porqué de ese monto
            3. Un tip práctico para cumplirlo

            RESPONDE SOLO EN JSON:
            {{
            "suggested_amount": float,
            "start_date": "{start_date}",
            "end_date": "{end_date}",
            "description": "...",
            "tip": "..."
            }}
        """)

        # Filtrar transacciones de la categoría
        cat_tx = [t for t in transactions if t.get("category_id") == category_id]
        tx_text = "\n".join([
            f"- {t.get('description', 'Sin descripción')}: ${t.get('amount', 0)} ({t.get('date', '')})" for t in cat_tx[-20:]
        ])

        try:
            chain = prompt | self.llm | JsonOutputParser()
            result = await chain.ainvoke({
                "category_id": category_id,
                "start_date": start_date,
                "end_date": end_date,
                "analysis": str(analysis),
                "transactions": tx_text,
                "profile": str(semantic_profile)
            })
            return result
        except Exception as e:
            return {
                "suggested_amount": 0,
                "start_date": start_date,
                "end_date": end_date,
                "description": "No se pudo sugerir un monto.",
                "tip": "Revisa tus hábitos de gasto.",
                "error": str(e)
            }

    async def review_budget(self, budget: Dict, transactions: List[Dict], financial_context: Dict, semantic_profile: Dict) -> Dict:
        """
        Revisa si el presupuesto se va a cumplir antes de la fecha de fin.
        Devuelve estado, tips, análisis de transacciones y sugerencias de cambio.
        """
        category_id = budget.get("category_id")
        amount = budget.get("amount")
        start_date = budget.get("start_date")
        end_date = budget.get("end_date")

        # Filtrar transacciones de la categoría y periodo
        cat_tx = [
            t for t in transactions
            if t.get("category_id") == category_id and start_date <= t.get("date", "") <= end_date
        ]
        spent = sum(t.get("amount", 0) for t in cat_tx)
        remaining = amount - spent

        prompt = ChatPromptTemplate.from_template("""
            Eres un asesor de presupuestos.
            El usuario tiene un presupuesto activo para una categoría.

            DATOS DEL PRESUPUESTO:
            - category_id: {category_id}
            - monto: ${amount}
            - fecha inicio: {start_date}
            - fecha fin: {end_date}
            - gastado hasta ahora: ${spent}
            - restante: ${remaining}

            TRANSACCIONES DE LA CATEGORÍA:
            {transactions}

            CONTEXTO FINANCIERO:
            {financial_context}

            PERFIL DEL USUARIO:
            {profile}

            Analiza:
            1. ¿El usuario va a cumplir el presupuesto antes de la fecha de fin? ("bien", "regular", "mal")
            2. Da tips para cumplirlo
            3. Analiza si los patrones de gasto son saludables o no
            4. Sugiere cambios para mejorar

            RESPONDE SOLO EN JSON:
            {{
            "status": "bien|regular|mal",
            "tips": ["..."],
            "analysis": "...",
            "patterns": ["..."],
            "suggested_changes": ["..."]
            }}
        """)

        tx_text = "\n".join([
            f"- {t.get('description', 'Sin descripción')}: ${t.get('amount', 0)} ({t.get('date', '')})" for t in cat_tx[-20:]
        ])

        try:
            chain = prompt | self.llm | JsonOutputParser()
            result = await chain.ainvoke({
                "category_id": category_id,
                "amount": amount,
                "start_date": start_date,
                "end_date": end_date,
                "spent": spent,
                "remaining": remaining,
                "transactions": tx_text,
                "financial_context": str(financial_context),
                "profile": str(semantic_profile)
            })
            return result
        except Exception as e:
            return {
                "status": "mal",
                "tips": ["Revisa tus gastos y ajusta tus hábitos."],
                "analysis": "No se pudo analizar el presupuesto.",
                "patterns": [],
                "suggested_changes": [],
                "error": str(e)
            }
