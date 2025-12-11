from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.config import settings

class FinancialAnalyzer:
    """
    Agente especializado en análisis financiero.
    Detecta gastos hormiga, fugas de dinero, y evalúa salud financiera.
    Usa semantic_profile para personalizar recomendaciones.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE
        )
    
    async def analyze(self,query: str,transactions: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """
        Ejecuta el análisis financiero según el tipo de consulta.
        Usa semantic_profile para personalizar el tono y enfoque del análisis.
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
        """
        Análisis de salud financiera general.
        Usa semantic_profile para adaptar el tono del mensaje.
        """
        
        # Adaptar tono según perfil
        tone = semantic_profile.get("preferred_tone", "friendly")
        literacy_level = semantic_profile.get("financial_literacy", "beginner")
        
        prompt = ChatPromptTemplate.from_template("""
            Eres un asesor financiero experto. Analiza la situación financiera del usuario.

            TONO A USAR: {tone}
            NIVEL DE CONOCIMIENTO FINANCIERO: {literacy_level}

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
            - Adapta tu lenguaje al nivel de conocimiento financiero del usuario
            - Usa el tono especificado
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
            "message": "Mensaje personalizado según tono y nivel del usuario"
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
                "tone": tone,
                "literacy_level": literacy_level,
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
        """
        Detecta gastos hormiga (pequeños gastos frecuentes).
        Usa semantic_profile para determinar el estilo motivacional.
        """
        
        motivation_style = semantic_profile.get("motivation_style", "balanced")
        risk_tolerance = semantic_profile.get("risk_tolerance", "medium")
        
        prompt = ChatPromptTemplate.from_template("""
            Eres un analista financiero especializado en detectar GASTOS HORMIGA.

            ESTILO MOTIVACIONAL DEL USUARIO: {motivation_style}
            TOLERANCIA AL RIESGO: {risk_tolerance}

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
            - Adapta tu mensaje al estilo motivacional del usuario
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
            "message": "Mensaje constructivo adaptado al estilo motivacional",
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
                "motivation_style": motivation_style,
                "risk_tolerance": risk_tolerance,
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
        """
        Detecta fugas de dinero (gastos anormales o crecientes).
        Usa semantic_profile para personalizar las alertas.
        """
        
        emotional_state = semantic_profile.get("emotional_state", "neutral")
        
        prompt = ChatPromptTemplate.from_template("""
            Eres un analista experto en detectar FUGAS DE DINERO.

            ESTADO EMOCIONAL DEL USUARIO: {emotional_state}
            (Adapta tu mensaje para no causar estrés adicional si ya está preocupado)

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
            "message": "Mensaje empático adaptado al estado emocional",
            "action_items": ["Acciones sugeridas"]
            }}
        """)
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            
            result = await chain.ainvoke({
                "emotional_state": emotional_state,
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
        """
        Analiza gastos repetitivos y suscripciones.
        Usa semantic_profile para priorizar recomendaciones.
        """
        
        spending_patterns = semantic_profile.get("spending_patterns", [])
        
        prompt = ChatPromptTemplate.from_template("""
            Analiza gastos REPETITIVOS y SUSCRIPCIONES.

            PATRONES DE GASTO CONOCIDOS: {patterns}

            TRANSACCIONES:
            {transactions}

            CONTEXTO:
            - Excedente mensual: ${surplus}

            Identifica:
            1. Gastos que se repiten mensualmente
            2. Frecuencia y monto promedio
            3. Impacto en el presupuesto mensual
            4. Alineación con patrones de gasto conocidos

            RESPONDE SOLO EN JSON:
            {{
            "repetitive_expenses": [
                {{
                "description": "Nombre del gasto",
                "frequency": "monthly|weekly",
                "average_amount": float,
                "annual_cost": float,
                "category_id": int,
                "matches_known_pattern": boolean
                }}
            ],
            "total_monthly_recurring": float,
            "message": "Resumen considerando patrones conocidos"
            }}
        """)
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            result = await chain.ainvoke({
                "patterns": str(spending_patterns),
                "transactions": str(transactions[-60:]),
                "surplus": financial_context.get("month_surplus", 0)
            })
            return result
        except Exception as e:
            return {
                "repetitive_expenses": [],
                "message": "No se detectaron gastos repetitivos.",
                "error": str(e)
            }