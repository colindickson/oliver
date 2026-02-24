FROM python:3.12-slim

WORKDIR /app

# Install shared package first
COPY shared/ /tmp/shared/
RUN pip install --no-cache-dir /tmp/shared && rm -rf /tmp/shared

COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp-server/ .

CMD ["python", "server.py"]
