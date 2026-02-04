#!/bin/bash

# Script to stop all development services
# Usage: ./dev-stop.sh

echo "🛑 Stopping PokerLite services..."

# Kill tmux session if it exists
if tmux has-session -t pokerlite 2>/dev/null; then
    tmux kill-session -t pokerlite
    echo "✅ Stopped tmux session"
else
    echo "⚠️  No tmux session found"
fi

# Also kill any stray uvicorn/vite processes
pkill -f "uvicorn.*8000" 2>/dev/null && echo "✅ Stopped lobby service"
pkill -f "uvicorn.*8001" 2>/dev/null && echo "✅ Stopped game service"  
pkill -f "vite.*5173" 2>/dev/null && echo "✅ Stopped frontend"

echo "✅ All services stopped"
