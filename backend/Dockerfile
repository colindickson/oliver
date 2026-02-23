FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

CMD ["sh", "-c", "until alembic upgrade head; do echo 'Waiting for DB...'; sleep 2; done && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
