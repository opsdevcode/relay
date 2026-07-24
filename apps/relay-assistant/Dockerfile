FROM python:3.12-slim

WORKDIR /app

COPY apps/relay-assistant/pyproject.toml apps/relay-assistant/
COPY apps/relay-assistant/src apps/relay-assistant/src
COPY apps/relay-assistant/tests apps/relay-assistant/tests
COPY knowledge knowledge
COPY packages packages
COPY catalog catalog

RUN pip install --no-cache-dir -e "apps/relay-assistant[dev]"

ENV PYTHONPATH=/app/apps/relay-assistant/src
WORKDIR /app/apps/relay-assistant

EXPOSE 8080
CMD ["uvicorn", "portal_assistant.main:app", "--host", "0.0.0.0", "--port", "8080"]
