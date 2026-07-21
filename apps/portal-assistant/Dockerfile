FROM python:3.12-slim

WORKDIR /app

COPY apps/portal-assistant/pyproject.toml apps/portal-assistant/
COPY apps/portal-assistant/src apps/portal-assistant/src
COPY apps/portal-assistant/tests apps/portal-assistant/tests
COPY knowledge knowledge
COPY packages packages
COPY catalog catalog

RUN pip install --no-cache-dir -e "apps/portal-assistant[dev]"

ENV PYTHONPATH=/app/apps/portal-assistant/src
WORKDIR /app/apps/portal-assistant

EXPOSE 8080
CMD ["uvicorn", "portal_assistant.main:app", "--host", "0.0.0.0", "--port", "8080"]
