# FINZEN IA Service - FastAPI skeleton

Este repositorio contiene un esqueleto mínimo para iniciar una API con FastAPI.

Requisitos
- Python 3.10+

Instalación (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Ejecutar el servidor (desarrollo)

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tests

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

Estructura

- `app/main.py`: instancia FastAPI y endpoint raíz
- `app/api/routes.py`: router de ejemplo (salud)
- `tests/test_main.py`: pruebas básicas con TestClient
Siguientes pasos sugeridos:
- Añadir configuración (pydantic Settings)
- Añadir logging y manejo de errores
- Añadir Dockerfile y CI

Docker
------

Se han añadido un `Dockerfile` y un `docker-compose.yml` básicos.

Construir y ejecutar con Docker (desde el directorio del proyecto):

```powershell
docker build -t finzen-ia-service:latest .
docker run --rm -p 8000:8000 finzen-ia-service:latest
```

Usando docker-compose:

```powershell
docker-compose up --build
```

Notas:
- El `Dockerfile` usa la imagen `python:3.11-slim` y copia el proyecto en `/usr/src/app`.
- `requirements.txt` se instala en la imagen para aprovechar la cache de capas.

Si quieres que intente construir la imagen desde aquí, dime y lo intento (necesito que Docker esté instalado en tu máquina).
