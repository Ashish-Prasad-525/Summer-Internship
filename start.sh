#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════
#  AI Document Intelligence System — Local Dev Quick Start
# ════════════════════════════════════════════════════════════
set -e

echo ""
echo "🧠 AI Document Intelligence System — Setup"
echo "─────────────────────────────────────────"

# ── Backend ───────────────────────────────────────────────────
echo ""
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "  ✅ Virtual environment created"
fi

source venv/bin/activate

pip install -r requirements.txt -q
echo "  ✅ Python dependencies installed"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "  ⚠️  Created .env from template — set OPENAI_API_KEY if using OpenAI LLM"
fi

mkdir -p data/uploads vectorstore/faiss_index logs

# Start backend in background
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  ✅ Backend started (PID $BACKEND_PID) → http://localhost:8000"
echo "  📖 API docs → http://localhost:8000/api/docs"

# ── Frontend ──────────────────────────────────────────────────
cd ../frontend
echo ""
echo "📦 Setting up frontend..."

npm install -q
echo "  ✅ Node modules installed"

npm run dev &
FRONTEND_PID=$!
echo "  ✅ Frontend started (PID $FRONTEND_PID) → http://localhost:3000"

echo ""
echo "══════════════════════════════════════════"
echo "  🚀 App running at http://localhost:3000  "
echo "══════════════════════════════════════════"
echo ""
echo "  Press Ctrl+C to stop both servers"
echo ""

# Wait and cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo '🔴 Servers stopped.'" EXIT
wait
