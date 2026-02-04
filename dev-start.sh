#!/bin/bash

# Simple script to start all services in background

set -e

echo "🚀 Starting PokerLite Development Environment"
echo ""

# Check if already running
if lsof -i:8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ Port 8000 already in use (lobby service running?)"
    echo "   Run ./dev-stop.sh first"
    exit 1
fi

# Get absolute path to project root
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Start services in background
echo "Starting lobby service (port 8000)..."
(cd "$PROJECT_ROOT/services/lobby" && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) > /tmp/pokerlite-lobby.log 2>&1 &
LOBBY_PID=$!

echo "Starting game service (port 8001)..."
(cd "$PROJECT_ROOT/services/game" && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001) > /tmp/pokerlite-game.log 2>&1 &
GAME_PID=$!

echo "Starting frontend (port 5173)..."
(cd "$PROJECT_ROOT/poker-client" && npm run dev) > /tmp/pokerlite-frontend.log 2>&1 &
FRONTEND_PID=$!

# Save PIDs
echo "$LOBBY_PID" > /tmp/pokerlite-lobby.pid
echo "$GAME_PID" > /tmp/pokerlite-game.pid
echo "$FRONTEND_PID" > /tmp/pokerlite-frontend.pid

sleep 2

echo ""
echo "✅ All services started!"
echo ""
echo "📊 Services:"
echo "   - Frontend: http://localhost:5173"
echo "   - Lobby:    http://localhost:8000/api/health"
echo "   - Game:     ws://localhost:8001"
echo ""
echo "📝 Watch logs:"
echo "   tail -f /tmp/pokerlite-lobby.log"
echo "   tail -f /tmp/pokerlite-game.log"
echo "   tail -f /tmp/pokerlite-frontend.log"
echo ""
echo "🛑 Stop all: ./dev-stop.sh"
echo ""
