from typing import Dict, List
from datetime import datetime, date
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.config import settings

class GoalAnalyzer:
    """
    Agente especializado en análisis de metas financieras.
    Sugiere, evalúa y monitorea el progreso de objetivos financieros.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE
        )
    
    async def analyze(self,user_id: int,query: str,goals: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """
        Ejecuta el análisis de metas según el tipo de consulta
        """
        query_lower = query.lower()
        
        if "sugerir" in query_lower or "nueva" in query_lower or "crear" in query_lower:
            return await self._suggest_goals(
                goals,
                financial_context,
                semantic_profile
            )
        elif "evaluar" in query_lower or "viable" in query_lower:
            return await self._evaluate_goal(
                query,
                goals,
                financial_context,
                semantic_profile
            )
        elif "progreso" in query_lower or "track" in query_lower:
            return await self._track_goals(
                goals,
                financial_context,
                semantic_profile
            )
        else:
            # Análisis general de metas
            return await self._general_analysis(
                goals,
                financial_context,
                semantic_profile
            )
    
    async def _suggest_goals(self,existing_goals: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """Sugiere nuevas metas financieras realistas"""
        
        prompt = ChatPromptTemplate.from_template("""
            Eres un asesor financiero experto en establecimiento de metas.

            CONTEXTO FINANCIERO:
            - Ingreso mensual: ${income}
            - Excedente mensual: ${surplus}

            PERFIL DEL USUARIO:
            {profile}

            METAS EXISTENTES:
            {existing_goals}

            Sugiere hasta 3 metas financieras que sean:
            1. REALISTAS según el excedente disponible
            2. MOTIVADORAS y alineadas con el perfil
            3. ESPECÍFICAS y medibles
            4. NO DUPLICADAS con las existentes

            Prioriza:
            - Fondo de emergencia (si no existe)
            - Metas que conviertan gastos en ahorros intencionales
            - Objetivos de crecimiento personal

            REGLAS:
            - No sugieras metas que excedan el excedente mensual
            - Sé empático y motivador
            - Evita presión o culpa

            RESPONDE SOLO EN JSON:
            {{
            "suggested_goals": [
                {{
                "name": "Nombre claro de la meta",
                "reason": "Por qué es relevante para este usuario",
                "estimated_target": float,
                "suggested_timeframe_months": int,
                "monthly_contribution": float,
                "category": "TRAVEL|EMERGENCY_FUND|EDUCATION|TECHNOLOGY|HOME|OTHER"
                }}
            ],
            "message": "Mensaje motivador personalizado",
            "next_steps": ["Pasos concretos para comenzar"]
            }}
        """)
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            
            result = await chain.ainvoke({
                "income": financial_context.get("monthly_income", 0),
                "surplus": financial_context.get("month_surplus", 0),
                "profile": str(semantic_profile),
                "existing_goals": str(existing_goals)
            })
            
            return result
            
        except Exception as e:
            print(f" Error suggesting goals: {e}")
            return {
                "suggested_goals": [],
                "message": "No se pudieron generar sugerencias en este momento.",
                "error": str(e)
            }
    
    async def _evaluate_goal(self,query: str,existing_goals: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """Evalúa la viabilidad de una meta propuesta"""
        
        prompt = ChatPromptTemplate.from_template("""
            Evalúa la VIABILIDAD de una meta financiera propuesta.

            CONSULTA DEL USUARIO:
            {query}

            CONTEXTO FINANCIERO:
            - Excedente mensual: ${surplus}
            - Estabilidad de ingresos: {income_stability}

            METAS EXISTENTES:
            {existing_goals}

            PERFIL:
            {profile}

            Evalúa si la meta es:
            1. Financieramente viable con el excedente actual
            2. Temporalmente realista
            3. Compatible con metas existentes
            4. Emocionalmente sostenible (sin crear estrés)

            DECISIONES:
            - Viable → viable: true + explicación
            - Viable con ajustes → viable: false + ajustes sugeridos
            - No viable → explicar por qué y qué hacer primero

            RESPONDE SOLO EN JSON:
            {{
            "viable": true|false,
            "confidence": "high|medium|low",
            "reason": "Explicación clara y empática",
            "suggested_adjustments": {{
                "target_amount": float,
                "timeframe_months": int,
                "monthly_contribution": float
            }},
            "message": "Mensaje motivador",
            "alternative_approach": "Sugerencia constructiva si no es viable"
            }}
        """)
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            
            result = await chain.ainvoke({
                "query": query,
                "surplus": financial_context.get("month_surplus", 0),
                "income_stability": "medium",  # Calcular esto idealmente
                "existing_goals": str(existing_goals),
                "profile": str(semantic_profile)
            })
            
            return result
            
        except Exception as e:
            print(f" Error evaluating goal: {e}")
            return {
                "viable": False,
                "reason": "No se pudo completar la evaluación.",
                "error": str(e)
            }
    
    async def _track_goals(self,goals: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """Monitorea el progreso de las metas existentes"""
        
        if not goals:
            return {
                "message": "No tienes metas activas. ¿Quieres que te sugiera algunas?",
                "goals_status": []
            }
        
        prompt = ChatPromptTemplate.from_template("""
            Analiza el PROGRESO de las metas financieras del usuario.

            METAS:
            {goals}

            CONTEXTO:
            - Excedente mensual disponible: ${surplus}

            Para cada meta, evalúa:
            1. Progreso actual (% completado)
            2. Tiempo transcurrido vs tiempo total
            3. Ritmo de ahorro (adelantado, en tiempo, atrasado)
            4. Proyección a la fecha límite

            Clasifica cada meta:
            - on_track: progreso adecuado
            - behind: necesita más esfuerzo (manejable)
            - critical: requiere reevaluación

            REGLAS:
            - Sé alentador, no crítico
            - Enfócate en logros, no solo en faltantes
            - Da feedback constructivo

            RESPONDE SOLO EN JSON:
            {{
            "goals_status": [
                {{
                "goal_id": int,
                "name": "...",
                "progress_percentage": float,
                "status": "on_track|behind|critical|completed",
                "time_elapsed_percentage": float,
                "projected_completion": "YYYY-MM-DD",
                "monthly_gap": float,
                "message": "Feedback personalizado",
                "recommended_action": "Acción específica"
                }}
            ],
            "overall_message": "Mensaje general motivador",
            "distribution_suggestion": {{
                "total_available": float,
                "allocations": [
                {{"goal_id": int, "amount": float, "reason": "..."}}
                ]
            }}
            }}
        """)
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            
            # Enriquecer metas con cálculos
            enriched_goals = []
            for goal in goals:
                saved = goal.get("saved_amount", 0)
                target = goal.get("target_amount", 1)
                progress = (saved / target) * 100 if target > 0 else 0
                
                enriched_goals.append({
                    **goal,
                    "progress_percentage": progress
                })
            
            result = await chain.ainvoke({
                "goals": str(enriched_goals),
                "surplus": financial_context.get("month_surplus", 0)
            })
            
            return result
            
        except Exception as e:
            print(f" Error tracking goals: {e}")
            return {
                "goals_status": [],
                "message": "No se pudo completar el seguimiento.",
                "error": str(e)
            }
    
    async def _general_analysis(self,goals: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """Análisis general del estado de las metas"""
        
        if not goals:
            return await self._suggest_goals(goals, financial_context, semantic_profile)
        
        return await self._track_goals(goals, financial_context, semantic_profile)