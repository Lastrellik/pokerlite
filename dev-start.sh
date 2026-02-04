#!/bin/bash

# Script to start all services for local development
# Usage: ./dev-start.sh

set -e

echo "🚀 Starting PokerLite Development Environment"
echo ""

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo "⚠️  tmux not installed - starting services in background"
    echo ""
    
    cd services/lobby && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    LOBBY_PID=$!
    
    cd ../game && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 &
    GAME_PID=$!
    
    cd ../../poker-client && npm run dev &
    FRONTEND_PID=$!
    
    echo "✅ Services started!"
    echo ""
    echo "📊 Services:"
    echo "   - Lobby:    http://localhost:8000"
    echo "   - Game:     http://localhost:8001"
    echo "   - Frontend: http://localhost:5173"
    echo ""
    echo "PIDs: Lobby=$LOBBY_PID Game=$GAME_PID Frontend=$FRONTEND_PID"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    trap "kill $LOBBY_PID $GAME_PID $FRONTEND_PID 2>/dev/null" EXIT
    wait
    
    exit 0
fi

SESSION="pokerlite"

# Kill existing session if it exists
tmux kill-session -t $SESSION 2>/dev/null || true

# Create new session
tmux new-session -d -s $SESSION -n "lobby"

# Window 0: Lobby service
tmux send-keys -t $SESSION:0 "cd services/lobby && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" C-m

# Window 1: Game service
tmux new-window -t $SESSION:1 -n "game"
tmux send-keys -t $SESSION:1 "cd services/game && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001" C-m

# Window 2: Frontend
tmux new-window -t $SESSION:2 -n "frontend"
tmux send-keys -t $SESSION:2 "cd poker-client && npm run dev" C-m

# Window 3: Shell
tmux new-window -t $SESSION:3 -n "shell"

echo "✅ Services starting in tmux session '$SESSION'"
echo ""
tmux attach-session -t $SESSION
