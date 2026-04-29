#!/bin/bash
set -e

echo "=== SMC/ICT Trading Analyzer ==="
echo ""

# Install backend deps
echo "[1/3] Installing Python dependencies..."
cd backend
pip install -r requirements.txt -q
cd ..

# Install frontend deps
echo "[2/3] Installing Node.js dependencies..."
cd frontend
npm install --silent
cd ..

# Start backend
echo "[3/3] Starting services..."
echo "  → Backend:  http://localhost:8000"
echo "  → Frontend: http://localhost:5173"
echo ""

# Start backend in background
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo "Press Ctrl+C to stop both services."
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

wait
