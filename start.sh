#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "AtelierCAD - Générateur de patrons T-shirt"
echo "===================================="

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 est requis."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Node.js et npm sont requis pour l'interface React."
  exit 1
fi

if [ ! -x "venv/bin/python" ]; then
  echo "Le virtualenv est absent. Créez-le puis installez requirements.txt avant de lancer ce script."
  exit 1
fi

if ! ./venv/bin/python -c "import fastapi, uvicorn, pydantic, ezdxf, shapely, reportlab" >/dev/null 2>&1; then
  echo "Les dépendances Python ne sont pas installées. Lancez : ./venv/bin/pip install -r requirements.txt"
  exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
  echo "Les dépendances frontend ne sont pas installées. Lancez : npm install --prefix frontend"
  exit 1
fi

cleanup() {
  kill "$API_PID" "$WEB_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "Démarrage de FastAPI sur http://localhost:8000"
./venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

echo "Démarrage de l'interface React sur http://localhost:5173"
npm --prefix frontend run dev &
WEB_PID=$!

wait
