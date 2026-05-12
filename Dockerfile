# Build React → FastAPI serves frontend/dist + /api (single service on Railway).
FROM node:20-bookworm-slim AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN cd frontend && npm ci
COPY frontend ./frontend
RUN cd frontend && npm run build

FROM python:3.12-slim-bookworm
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY --from=frontend /app/frontend/dist ./frontend/dist

ENV PYTHONUNBUFFERED=1

# Railway sets PORT; default 8000 for local docker run.
CMD sh -c 'uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"'
