# Development Guide

This guide covers local development setup, testing, and project structure for PokerLite.

## Local Development Setup

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- npm

### Automated Setup (Recommended)

Start all services with hot-reload:

```bash
# Start all services (lobby, game, frontend)
./dev-start.sh

# Stop all services
./dev-stop.sh
```

**Services will be available at:**
- Frontend: http://localhost:5173
- Lobby API: http://localhost:8000
- Game WebSocket: ws://localhost:8001

### Manual Setup

**Lobby Service:**

```bash
cd services/lobby

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run lobby service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Game Service** (in a separate terminal):

```bash
cd services/game

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (including shared module)
pip install -r requirements.txt
pip install -e ../shared

# Run game service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**Frontend** (in a separate terminal):

```bash
cd poker-client

# Install dependencies
npm install

# Run the development server
npm run dev
```

## Configuration

### Backend (.env in project root)

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000

# CORS (comma-separated origins for development)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Authentication
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database (SQLite by default, PostgreSQL for production)
DATABASE_URL=sqlite:///./pokerlite.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/pokerlite
```

### Frontend (.env in poker-client/)

```bash
# API and WebSocket URLs
VITE_LOBBY_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8001
```

Create these files from examples:
```bash
cp .env.example .env
cp poker-client/.env.example poker-client/.env
```

## Project Structure

```
pokerlite/
├── services/
│   ├── shared/            # Shared poker logic & models
│   │   ├── models/        # Player, TableConfig
│   │   ├── poker/         # Poker logic, hand evaluation
│   │   └── setup.py
│   ├── lobby/             # Lobby service (HTTP REST)
│   │   ├── app/
│   │   │   ├── routes/    # Table CRUD, auth endpoints
│   │   │   ├── storage/   # In-memory/PostgreSQL storage
│   │   │   └── main.py
│   │   ├── tests/         # 25 tests
│   │   └── Dockerfile
│   └── game/              # Game service (WebSocket)
│       ├── app/
│       │   ├── core/      # Game logic, poker rules
│       │   ├── routes/    # WebSocket routes
│       │   └── main.py
│       ├── tests/         # 236 tests
│       └── Dockerfile
├── poker-client/          # React frontend
│   ├── src/
│   │   ├── components/    # Lobby, GamePage, PokerTable
│   │   ├── hooks/         # usePokerGame, useLobby
│   │   └── App.jsx        # React Router setup
│   └── package.json
├── e2e-tests/             # End-to-end browser tests
│   ├── e2e/
│   │   ├── specs/         # Test scenarios
│   │   ├── pageobjects/   # Page Object Model
│   │   ├── helpers/       # API helpers
│   │   └── fixtures/      # Test data
│   └── package.json       # E2E test dependencies
├── docker-compose.yml     # Multi-service orchestration
├── dev-start.sh           # Start all services locally
└── dev-stop.sh            # Stop all services
```

## Running Tests

### Backend Tests

**Game Service (236 tests):**
```bash
cd services/game
source .venv/bin/activate
pytest tests/ -v
```

**Lobby Service (25 tests):**
```bash
cd services/lobby
source .venv/bin/activate
pytest tests/ -v
```

### Frontend Tests

**Run all frontend tests (127 tests):**
```bash
cd poker-client
npm test
```

**Run specific test file:**
```bash
npm test -- src/components/Lobby.test.jsx
```

### E2E Tests (WebdriverIO)

**Prerequisites:**
```bash
# Make sure all services are running
./dev-start.sh

# Install E2E test dependencies (first time only)
cd e2e-tests
npm install
```

**Run E2E tests:**
```bash
# Headed mode (watch tests run)
npm run test:e2e

# Headless mode (CI/automated)
HEADLESS=true npm run test:e2e

# Run specific test file
npm run test:e2e -- --spec=e2e/specs/auth-flow.e2e.js
```

**E2E test features:**
- Real browser automation with Firefox
- Tests complete gameplay flows (join, start hand, betting, showdown)
- Authentication flow testing (registration, login, logout, token validation)
- Deterministic deck shuffling (seeded RNG for reproducible scenarios)
- Test-only API endpoints for configuration and state verification
- Headed mode by default for debugging, headless for CI

### Test Coverage Summary

**Total: 390+ tests passing ✅**
- Backend: 261 tests (game + lobby + auth)
- Frontend: 127 tests (components + hooks + auth)
- E2E: 3 tests (authentication flows)

## Building for Production

### Build Frontend Only

```bash
cd poker-client
npm run build
```

The built files will be in `poker-client/dist/`

### Build Docker Image

```bash
docker build -t pokerlite .
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment instructions.
