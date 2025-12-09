# Financial Insight Agent

This agent mirrors the structure of `goal_agent` and provides financial insights:

- Detecta gastos hormiga
- Detecta gastos repetitivos
- Evalúa salud financiera
- Detecta fugas de dinero

Usage:

1. Configure `.env` with Postgres and OpenAI credentials (same vars as `goal_agent`):

```
EPISODIC_DB_HOST=...
EPISODIC_DB_PORT=...
EPISODIC_DB_NAME=...
EPISODIC_DB_USER=...
EPISODIC_DB_PASSWORD=...
OPENAI_API_KEY=...
OPENAI_MODEL=...
LOG_LEVEL=INFO
```

2. Run locally:

```powershell
python -m financial_agent.agent_runner input.json
```

`input.json` should match the orchestrator input schema described in the project.
