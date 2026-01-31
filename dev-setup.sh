#!/bin/bash

# PokerLite Local Development Setup Script

set -e

echo "🎰 PokerLite Development Setup"
echo "==============================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

echo "✅ Python version: $(python3 --version)"
echo "✅ Node version: $(node --version)"
echo ""

# Setup backend
echo "📦 Setting up backend..."
cd server

if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "Installing Python dependencies..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

cd ..

# Setup frontend
echo ""
echo "📦 Setting up frontend..."
cd poker-client

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
else
    echo "Node modules already installed, skipping..."
fi

cd ..

# Create .env files if they don't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file from example..."
    cp .env.example .env
fi

if [ ! -f "poker-client/.env" ]; then
    echo "📝 Creating frontend .env file from example..."
    cp poker-client/.env.example poker-client/.env
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo "  1. Backend:  cd server && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "  2. Frontend: cd poker-client && npm run dev"
echo ""
echo "Or use the dev-start.sh script to start both automatically."
