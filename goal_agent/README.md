# Goal Intelligence Agent (CrewAI)

Agent encargado de gestión, evaluación y ajuste de metas financieras.

Estructura:
- `crew.py` - inicializador del servicio/agent (CrewAI wrapper)
- `agent.py` - definición principal del Goal Intelligence Agent
- `tasks/` - tareas que implementan cada acción (discover, evaluate, adjust, track)
- `tools/` - herramientas reutilizables (DB, ATR, fechas, distribución emocional)
- `utils/` - utilidades (logging, validators)
- `models/` - Pydantic models de entrada/salida

Setup rápido

1. Crear un virtualenv e instalar dependencias:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2. Configurar variables de entorno (ver `.env.example` en repo)

3. Ejecutar `python -m goal_agent.agent_runner` para pruebas locales (ejemplo incluido)

Nota: Este proyecto asume que usarás OpenAI como LLM. Ajusta `OPENAI_API_KEY`.
