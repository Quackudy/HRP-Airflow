#!/bin/bash

# HRP Portfolio Platform Startup Script

# --- Cleanup function ---
# This function will be called when the script exits (e.g., on Ctrl+C)
cleanup() {
    echo ""
    echo "Stopping services..."
    # Kill the processes by their PID
    # The 'kill 0' command sends the signal to all processes in the group
    # This is a robust way to clean up child processes
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null
    fi
    echo "All services stopped."
}

# 'trap' catches the SIGINT (Ctrl+C) and SIGTERM signals and runs the 'cleanup' function
trap cleanup SIGINT SIGTERM

echo "Starting HRP Portfolio Platform..."

# Set environment variables
export JWT_SECRET="your-secret-key-change-in-production"
export JWT_ALGORITHM="HS256"

# Prefer PostgreSQL, but fall back to SQLite if 5432 is not reachable
if timeout 1 bash -c 'cat < /dev/null > /dev/tcp/127.0.0.1/5432' 2>/dev/null; then
    # PostgreSQL URLs
    export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/hrp"
    export ASYNC_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/hrp"
    echo "Using PostgreSQL at localhost:5432"
else
    # SQLite URLs
    export DATABASE_URL="sqlite:///hrp.db"
    export ASYNC_DATABASE_URL="sqlite+aiosqlite:///hrp.db"
    echo "Postgres not reachable. Using SQLite at $DATABASE_URL"
fi

# Activate virtual environment
source .venv/bin/activate

# Start FastAPI backend
echo "Starting FastAPI backend on http://localhost:8000"
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# === FRONTEND CHANGES ARE HERE ===

# Start Next.js frontend
echo "Starting Next.js frontend on http://localhost:3000" # <-- CHANGED PORT
cd frontend
# CHANGED from VITE_API_URL to NEXT_PUBLIC_API_URL
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev &
FRONTEND_PID=$!

# === END OF CHANGES ===

echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Platform is running:"
echo "- Backend API: http://localhost:8000"
echo "- Frontend:    http://localhost:3000" # <-- CHANGED PORT
echo "- API Docs:    http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# 'wait' will pause the script here.
# The 'trap' will handle cleanup when Ctrl+C is pressed.
wait "$BACKEND_PID"
wait "$FRONTEND_PID"
