#!/bin/bash
# Run all tests for pokerlite (backend + frontend)

set -e  # Exit on first error

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "Running Pokerlite Tests"
echo "======================================"

# Backend tests
echo ""
echo "🐍 Backend Tests (Python)"
echo "--------------------------------------"
cd "$PROJECT_ROOT/server"
source .venv/bin/activate
python -m pytest "${@:---tb=short}"

# Frontend tests
echo ""
echo "⚛️  Frontend Tests (React)"
echo "--------------------------------------"
cd "$PROJECT_ROOT/poker-client"
npm test -- --run

echo ""
echo "======================================"
echo "✅ All tests passed!"
echo "======================================"
