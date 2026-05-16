FROM python:3.11-slim

WORKDIR /app

# Copiar dependencias
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código compartido del backend
COPY backend/config.py .
COPY backend/logging_config.py .
COPY backend/middleware/ ./middleware/
COPY backend/messaging/ ./messaging/
COPY backend/redis_client.py .
COPY backend/services/ ./services/
COPY backend/models.py .
COPY backend/schemas.py .
COPY backend/database.py .

# Copiar entrypoint del worker
COPY worker/main.py .

CMD ["python", "main.py"]