from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.config import settings

class FinancialAnalyzer:
    """
    Agente especializado en análisis financiero.
    Detecta gastos hormiga, fugas de dinero, y evalúa salud financiera.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE
        )
    
    async def analyze(self,user_id: int,query: str,transactions: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """
        Ejecuta el análisis financiero según el tipo de consulta
        """
        query_lower = query.lower()
        
        # Router interno: decide qué tipo de análisis hacer
        if "hormiga" in query_lower or "pequeños" in query_lower:
            return await self._analyze_ant_expenses(
                transactions,
                financial_context,
                semantic_profile
            )
        elif "fuga" in query_lower or "leak" in query_lower:
            return await self._analyze_leaks(
                transactions,
                financial_context,
                semantic_profile
            )
        elif "repetitiv" in query_lower or "recurrent" in query_lower:
            return await self._analyze_repetitive(
                transactions,
                financial_context,
                semantic_profile
            )
        else:
            # Análisis general de salud financiera
            return await self._analyze_health(
                transactions,
                financial_context,
                semantic_profile
            )
    
    async def _analyze_health(self,transactions: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """Análisis de salud financiera general"""
        
        prompt = ChatPromptTemplate.from_template("""
            Eres un asesor financiero experto. Analiza la situación financiera del usuario.

            CONTEXTO FINANCIERO:
            - Ingreso mensual: ${income}
            - Gastos variables: ${expenses}
            - Excedente mensual: ${surplus}

            PERFIL DEL USUARIO:
            {profile}

            TRANSACCIONES RECIENTES (últimas 15):
            {transactions}

            Analiza:
            1. Estabilidad de ingresos
            2. Balance entre gastos fijos y variables
            3. Capacidad de ahorro
            4. Señales de estrés financiero
            5. Categorías con mayor gasto

            REGLAS:
            - No uses juicios de valor
            - Sé objetivo y basado en datos
            - Identifica patrones específicos
            - Proporciona métricas útiles

            RESPONDE SOLO EN JSON:
            {{
            "health_score": 0-100,
            "health_status": "excellent|good|fair|poor",
            "monthly_surplus": float,
            "income_stability": "high|medium|low",
            "top_spending_categories": [
                {{"category_id": int, "amount": float, "percentage": float}}
            ],
            "risk_flags": ["..."],
            "recommendations": ["..."],
            "message": "Mensaje amigable y motivador para el usuario"
            }}
        """)
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            
            # Preparar transacciones (últimas 15)
            recent_tx = transactions[-15:] if len(transactions) > 15 else transactions
            tx_summary = "\n".join([
                f"- {t.get('description', 'Sin descripción')}: ${t.get('amount', 0)} ({t.get('type', 'EXPENSE')})"
                for t in recent_tx
            ])
            
            result = await chain.ainvoke({
                "income": financial_context.get("monthly_income", 0),
                "expenses": financial_context.get("variable_expenses", 0),
                "surplus": financial_context.get("month_surplus", 0),
                "profile": str(semantic_profile),
                "transactions": tx_summary
            })
            
            return result
            
        except Exception as e:
            print(f" Error in health analysis: {e}")
            return {
                "health_score": 50,
                "health_status": "unknown",
                "message": "No se pudo completar el análisis. Intenta de nuevo.",
                "error": str(e)
            }
    
    async def _analyze_ant_expenses(self,transactions: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """Detecta gastos hormiga (pequeños gastos frecuentes)"""
        
        prompt = ChatPromptTemplate.from_template("""
            Eres un analista financiero especializado en detectar GASTOS HORMIGA.

            Los gastos hormiga son:
            - Compras pequeñas y frecuentes
            - Bajo valor individual pero alto impacto acumulado
            - Generalmente no planificados
            - Reducen capacidad de ahorro

            TRANSACCIONES:
            {transactions}

            CONTEXTO:
            - Ingreso mensual: ${income}
            - Excedente: ${surplus}

            Detecta patrones de gastos hormiga:
            1. Agrupa transacciones similares
            2. Calcula frecuencia e impacto mensual
            3. Identifica si es habitual u ocasional

            REGLAS:
            - No moralices el gasto
            - Sé objetivo y constructivo
            - Enfócate en el impacto acumulado

            RESPONDE SOLO EN JSON:
            {{
            "ant_expenses": [
                {{
                "pattern_description": "Ej: Cafés diarios",
                "categories": [1, 2],
                "frequency": "daily|weekly",
                "monthly_estimated_impact": float,
                "behavioral_signal": "habitual|occasional",
                "transaction_count": int
                }}
            ],
            "total_monthly_impact": float,
            "message": "Mensaje constructivo y amigable",
            "suggestions": ["Sugerencias prácticas sin presión"]
            }}
        """)
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            
            # Filtrar solo gastos pequeños y frecuentes
            small_expenses = [
                t for t in transactions 
                if t.get("type") == "EXPENSE" 
                and t.get("amount", 0) < settings.ANT_EXPENSE_THRESHOLD
            ]
            
            tx_text = "\n".join([
                f"- {t.get('description')}: ${t.get('amount')} ({t.get('date')})"
                for t in small_expenses[-30:]  # Últimos 30 gastos pequeños
            ])
            
            result = await chain.ainvoke({
                "transactions": tx_text,
                "income": financial_context.get("monthly_income", 0),
                "surplus": financial_context.get("month_surplus", 0)
            })
            
            return result
            
        except Exception as e:
            print(f" Error in ant expenses analysis: {e}")
            return {
                "ant_expenses": [],
                "message": "No se detectaron gastos hormiga significativos.",
                "error": str(e)
            }
    
    async def _analyze_leaks(self,transactions: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """Detecta fugas de dinero (gastos anormales o crecientes)"""
        
        prompt = ChatPromptTemplate.from_template("""
            Eres un analista experto en detectar FUGAS DE DINERO.

            Las fugas son:
            - Gastos anormalmente altos
            - Categorías con crecimiento no justificado
            - Patrones de gasto que no se alinean con ingresos

            TRANSACCIONES:
            {transactions}

            CONTEXTO:
            - Ingreso: ${income}
            - Excedente: ${surplus}

            Detecta:
            1. Picos anormales de gasto
            2. Categorías con tendencia creciente
            3. Gastos que impactan el excedente

            RESPONDE SOLO EN JSON:
            {{
            "money_leaks": [
                {{
                "category_id": int,
                "detected_pattern": "Descripción del patrón",
                "monthly_impact": float,
                "severity": "high|medium|low"
                }}
            ],
            "total_leak_impact": float,
            "message": "Mensaje amigable",
            "action_items": ["Acciones sugeridas"]
            }}
        """)
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            
            result = await chain.ainvoke({
                "transactions": str(transactions[-30:]),
                "income": financial_context.get("monthly_income", 0),
                "surplus": financial_context.get("month_surplus", 0)
            })
            
            return result
            
        except Exception as e:
            print(f" Error in leaks analysis: {e}")
            return {
                "money_leaks": [],
                "message": "No se detectaron fugas significativas.",
                "error": str(e)
            }
    
    async def _analyze_repetitive(self,transactions: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """Analiza gastos repetitivos y suscripciones"""
        
        prompt = ChatPromptTemplate.from_template("""
            Analiza gastos REPETITIVOS y SUSCRIPCIONES.

            TRANSACCIONES:
            {transactions}

            Identifica:
            1. Gastos que se repiten mensualmente
            2. Frecuencia y monto promedio
            3. Impacto en el presupuesto mensual

            RESPONDE SOLO EN JSON:
            {{
            "repetitive_expenses": [
                {{
                "description": "Nombre del gasto",
                "frequency": "monthly|weekly",
                "average_amount": float,
                "annual_cost": float,
                "category_id": int
                }}
            ],
            "total_monthly_recurring": float,
            "message": "Resumen amigable"
            }}
        """)
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            result = await chain.ainvoke({"transactions": str(transactions[-60:])})
            return result
        except Exception as e:
            return {"repetitive_expenses": [], "error": str(e)}