Carpeta `app/services/`

Qué irá aquí:
- Lógica de negocio y orquestación (p. ej. `chat_service.py`): mantener el estado, formatear prompts, procesar respuestas.
- Validaciones y transformaciones que no pertenezcan directamente a los endpoints.

Propósito:
- Mantener la lógica de dominio separada de la capa de I/O (clients) y de los endpoints (api).
