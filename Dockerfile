FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# FastAPI application
COPY backend/api/ ./api/

# Riot API rank sync module
COPY backend/lolapp_rank_sync.py ./


EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]