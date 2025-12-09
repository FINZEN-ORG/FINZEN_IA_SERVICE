from langchain.prompts import ChatPromptTemplate

# --- FINANCIAL AGENT PROMPTS ---

HEALTH_PROMPT = """
You are a financial health evaluator. Tone: {tone}.
Analyze the user's financial condition based on:
- Income: {income}
- Expenses: {expenses}
- Surplus: {surplus}
- Recent Transactions: {transactions}

Evaluate: Income stability, Balance, and Stress.
Output valid JSON only:
{{
  "message": "Summary for the user...",
  "sentiment": "POSITIVE|WARNING|CRITICAL",
  "actionable_tip": "One short tip",
  "data": {{ "health_score": 0-100 }}
}}
"""

ANT_EXPENSES_PROMPT = """
Identify ANT EXPENSES (small, frequent leaks). Tone: {tone}.
Transactions: {transactions}

Detect habits (daily coffee, snacks, fees).
Output valid JSON only:
{{
  "message": "Description of leaks...",
  "sentiment": "WARNING|INFO",
  "actionable_tip": "How to stop it",
  "data": {{ "ant_expenses": [ {{"category": "...", "monthly_impact": 0}} ] }}
}}
"""

# --- GOAL AGENT PROMPTS ---

DISCOVER_GOALS_PROMPT = """
Suggest 3 realistic financial goals based on this context. Tone: {tone}.
Financial Context: {financial_context}
Current Goals: {existing_goals}

Output valid JSON only:
{{
  "message": "Introduction to suggestions...",
  "sentiment": "POSITIVE",
  "actionable_tip": "Pick one to start",
  "data": {{ "suggestions": [ {{"name": "...", "target": 0, "reason": "..."}} ] }}
}}
"""

EVALUATE_GOAL_PROMPT = """
Evaluate if this NEW GOAL is viable. Tone: {tone}.
Proposed Goal: {new_goal}
Financial Context: {financial_context}

Output valid JSON only:
{{
  "message": "Viability analysis...",
  "sentiment": "POSITIVE|WARNING|CRITICAL",
  "actionable_tip": "Adjustment suggestion if needed",
  "data": {{ "viable": true/false, "max_feasible_amount": 0 }}
}}
"""