#!/bin/bash

# HRP Portfolio Platform Startup Script

echo "Starting HRP Portfolio Platform..."

# Set environment variables
export JWT_SECRET="your-secret-key-change-in-production"
export JWT_ALGORITHM="HS256"

# Prefer PostgreSQL, but fall back to SQLite if 5432 is not reachable
if timeout 1 bash -c 'cat < /dev/null > /dev/tcp/127.0.0.1/5432' 2>/dev/null; then
  export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/hrp"
  echo "Using PostgreSQL at localhost:5432"
else
  export DATABASE_URL="sqlite:////mnt/c/Users/passa/VScodeProject/HRP/hrp.db"
  echo "Postgres not reachable. Using SQLite at $DATABASE_URL for API only"
fi

# Activate virtual environment
source .venv/bin/activate

# Start FastAPI backend
echo "Starting FastAPI backend on http://localhost:8000"
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start React frontend
echo "Starting React frontend on http://localhost:5173"
cd frontend
VITE_API_URL=http://localhost:8000 npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Platform is running:"
echo "- Backend API: http://localhost:8000"
echo "- Frontend: http://localhost:5173"
echo "- API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait
