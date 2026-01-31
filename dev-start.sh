#!/bin/bash

# PokerLite Development Startup Script
# Starts both backend and frontend in development mode

set -e

echo "🎰 Starting PokerLite Development Servers"
echo "========================================="
echo ""

# Check if setup has been run
if [ ! -d "server/.venv" ]; then
    echo "❌ Virtual environment not found. Please run ./dev-setup.sh first."
    exit 1
fi

if [ ! -d "poker-client/node_modules" ]; then
    echo "❌ Node modules not found. Please run ./dev-setup.sh first."
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "🚀 Starting backend server on http://localhost:8000"
cd server
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Give backend a moment to start
sleep 2

# Start frontend
echo "🚀 Starting frontend dev server on http://localhost:5173"
cd poker-client
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both servers are running!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
