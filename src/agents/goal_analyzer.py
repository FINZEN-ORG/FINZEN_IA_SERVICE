from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.config import settings

class GoalAnalyzer:
    """
    Agente especializado en análisis de metas financieras.
    Sugiere, evalúa y monitorea el progreso de objetivos financieros.
    Usa semantic_profile para personalizar recomendaciones.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE
        )
    
    async def analyze(self,query: str,goals: List[Dict],financial_context: Dict,semantic_profile: Dict) -> Dict:
        """
        Ejecuta el análisis de metas según el tipo de consulta.
        Usa semantic_profile para personalizar el enfoque y tono.
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
        """
        Sugiere nuevas metas financieras realistas.
        Usa semantic_profile para personalizar las sugerencias según
        tolerancia al riesgo y estilo motivacional.
        """
        
        risk_tolerance = semantic_profile.get("risk_tolerance", "medium")
        motivation_style = semantic_profile.get("motivation_style", "balanced")
        preferred_categories = semantic_profile.get("preferred_categories", [])
        
        prompt = ChatPromptTemplate.from_template("""
            Eres un asesor financiero experto en establecimiento de metas.

            PERFIL DEL USUARIO:
            - Tolerancia al riesgo: {risk_tolerance}
            - Estilo motivacional: {motivation_style}
            - Categorías preferidas: {preferred_categories}

            CONTEXTO FINANCIERO:
            - Ingreso mensual: ${income}
            - Excedente mensual: ${surplus}

            PERFIL COMPLETO:
            {profile}

            METAS EXISTENTES:
            {existing_goals}

            Sugiere hasta 3 metas financieras que sean:
            1. REALISTAS según el excedente y perfil de riesgo
            2. MOTIVADORAS y alineadas con el estilo motivacional
            3. ESPECÍFICAS y medibles
            4. NO DUPLICADAS con las existentes

            Prioriza según el perfil:
            - risk_tolerance: high → metas ambiciosas | low → metas conservadoras
            - motivation_style: goal_oriented → metas específicas | stress_averse → metas flexibles

            REGLAS:
            - No sugieras metas que excedan el excedente mensual
            - Sé empático y motivador según el estilo
            - Evita presión o culpa

            RESPONDE SOLO EN JSON:
            {{
            "suggested_goals": [
                {{
                "name": "Nombre claro de la meta",
                "reason": "Por qué es relevante para este usuario específico",
                "estimated_target": float,
                "suggested_timeframe_months": int,
                "monthly_contribution": float,
                "category": "TRAVEL|EMERGENCY_FUND|EDUCATION|TECHNOLOGY|HOME|OTHER",
                "risk_alignment": "Explicar cómo se alinea con su perfil de riesgo"
                }}
            ],
            "message": "Mensaje motivador personalizado según estilo",
            "next_steps": ["Pasos concretos considerando su perfil"]
            }}
        """)
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            
            result = await chain.ainvoke({
                "risk_tolerance": risk_tolerance,
                "motivation_style": motivation_style,
                "preferred_categories": str(preferred_categories),
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
        """
        Evalúa la viabilidad de una meta propuesta.
        Considera el perfil de riesgo y estado emocional del usuario.
        """
        
        risk_tolerance = semantic_profile.get("risk_tolerance", "medium")
        emotional_state = semantic_profile.get("emotional_state", "neutral")
        
        prompt = ChatPromptTemplate.from_template("""
            Evalúa la VIABILIDAD de una meta financiera propuesta.

            PERFIL DEL USUARIO:
            - Tolerancia al riesgo: {risk_tolerance}
            - Estado emocional: {emotional_state}

            CONSULTA DEL USUARIO:
            {query}

            CONTEXTO FINANCIERO:
            - Excedente mensual: ${surplus}
            - Estabilidad de ingresos: {income_stability}

            METAS EXISTENTES:
            {existing_goals}

            PERFIL COMPLETO:
            {profile}

            Evalúa si la meta es:
            1. Financieramente viable con el excedente actual
            2. Temporalmente realista
            3. Compatible con metas existentes
            4. Emocionalmente sostenible según el perfil

            Considera:
            - Si risk_tolerance es low, prioriza estabilidad
            - Si emotional_state es stressed, sugiere metas menos presionantes

            DECISIONES:
            - Viable → viable: true + explicación
            - Viable con ajustes → viable: false + ajustes considerando perfil
            - No viable → explicar por qué y qué hacer primero

            RESPONDE SOLO EN JSON:
            {{
            "viable": true|false,
            "confidence": "high|medium|low",
            "reason": "Explicación clara considerando su perfil",
            "suggested_adjustments": {{
                "target_amount": float,
                "timeframe_months": int,
                "monthly_contribution": float
            }},
            "message": "Mensaje empático según estado emocional",
            "alternative_approach": "Sugerencia alineada con su perfil de riesgo"
            }}
        """)
        
        try:
            chain = prompt | self.llm | JsonOutputParser()
            
            result = await chain.ainvoke({
                "risk_tolerance": risk_tolerance,
                "emotional_state": emotional_state,
                "query": query,
                "surplus": financial_context.get("month_surplus", 0),
                "income_stability": "medium",
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
        """
        Monitorea el progreso de las metas existentes.
        Usa semantic_profile para dar feedback apropiado.
        """
        
        if not goals:
            return {
                "message": "No tienes metas activas. ¿Quieres que te sugiera algunas?",
                "goals_status": []
            }
        
        motivation_style = semantic_profile.get("motivation_style", "balanced")
        preferred_tone = semantic_profile.get("preferred_tone", "friendly")
        
        prompt = ChatPromptTemplate.from_template("""
            Analiza el PROGRESO de las metas financieras del usuario.

            PERFIL:
            - Estilo motivacional: {motivation_style}
            - Tono preferido: {preferred_tone}

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

            Adapta el feedback según:
            - motivation_style: goal_oriented → enfoque en logros | stress_averse → enfoque en calma
            - preferred_tone: friendly → casual | encouraging → motivador

            REGLAS:
            - Sé alentador según el estilo preferido
            - Enfócate en logros, no solo en faltantes
            - Da feedback constructivo adaptado al tono

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
                "message": "Feedback personalizado según estilo y tono",
                "recommended_action": "Acción específica adaptada al perfil"
                }}
            ],
            "overall_message": "Mensaje general según estilo motivacional",
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
                "motivation_style": motivation_style,
                "preferred_tone": preferred_tone,
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