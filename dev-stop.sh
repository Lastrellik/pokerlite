#!/bin/bash

echo "🛑 Stopping PokerLite services..."

# Stop using PID files
for service in lobby game frontend; do
    if [ -f "/tmp/pokerlite-${service}.pid" ]; then
        PID=$(cat /tmp/pokerlite-${service}.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID 2>/dev/null && echo "✅ Stopped ${service} (PID $PID)"
        fi
        rm /tmp/pokerlite-${service}.pid
    fi
done

# Fallback: kill by port
pkill -f "uvicorn.*8000" 2>/dev/null && echo "✅ Killed lobby on port 8000"
pkill -f "uvicorn.*8001" 2>/dev/null && echo "✅ Killed game on port 8001"
pkill -f "vite.*5173" 2>/dev/null && echo "✅ Killed frontend on port 5173"

# Kill any tmux session too
tmux kill-session -t pokerlite 2>/dev/null && echo "✅ Killed tmux session"

echo "✅ All services stopped"
