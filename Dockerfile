# Usamos una imagen ligera de Python 3.11
FROM python:3.11-slim
# Evita que Python escriba archivos .pyc y fuerza logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
# Instalar dependencias del sistema necesarias para compilar psycopg2 (si fuera necesario)
# Para psycopg2-binary usualmente no hace falta, pero es bueno tenerlo por si acaso.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
# Copiar requirements primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copiar el código fuente
COPY . .
# Crear un usuario no-root por seguridad (Azure lo recomienda)
# RUN useradd -m appuser && chown -R appuser /app
# USER appuser
# Exponer el puerto
EXPOSE 8000
# Comando de arranque apuntando a src.main:app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]