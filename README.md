# PokerLite 🎰

A real-time multiplayer poker application built with FastAPI (Python) and React.

> **Note**: This project was developed with AI assistance using Claude Code, demonstrating modern AI-augmented development workflows. See commit history for co-authorship details.

## Features

### Authentication & User Management
- **User registration and login** - Secure account creation with JWT authentication
- **Persistent chip stacks** - Players maintain chip count across sessions
- **Database integration** - SQLite for development, PostgreSQL-ready for production
- **Token expiration handling** - Automatic logout and re-authentication prompts
- **Guest mode** - Play without registration (non-persistent stacks)
- **Lobby authentication** - Login/signup directly from lobby without joining tables

### Lobby System
- **Table browser** - Browse and join active tables
- **Create tables** - Customizable blinds, player limits, and turn timeouts
- **Auto-refresh** - Table list updates every 5 seconds

### Gameplay
- Real-time multiplayer Texas Hold'em poker
- WebSocket-based communication for instant updates
- Clean, modern React UI with elliptical table layout
- Up to 8 players per table with automatic seat assignment
- **Advanced side pot system**:
  - Real-time side pot breakdown display during hands
  - Correctly handles multiple side pots with different stack sizes
  - Shows pot amounts and eligible players for each pot
  - Detailed side pot breakdown in showdown results
- **Stack persistence** - Players keep their chip count when disconnecting/reconnecting
- **Detailed game log** - Shows all actions, street changes, and pot distributions
- **Auto-delete empty tables** - Tables clean up automatically when all players leave
- Spectator mode for watching games in progress
- Waitlist system with automatic promotion when seats open
- Turn timeout with auto-fold/check
- All-in runout with card-by-card reveal animations
- **Clear all-in indicators** - Shows when calling is an all-in action

### Technical
- Microservices architecture (lobby + game services)
- **JWT-based authentication** with secure password hashing (bcrypt)
- **SQLAlchemy ORM** with SQLite/PostgreSQL support
- **Database migrations** with Alembic
- Shared poker logic module
- Comprehensive test coverage (260+ tests: unit, integration, auth, E2E)
- **Deterministic deck shuffling** for reproducible testing
- E2E browser automation with WebdriverIO
- Docker support for easy deployment
- Debug logging for side pot calculations

## Architecture

```
┌─────────────────┐
│  Lobby Service  │  (HTTP REST - Port 8000)
│  - Auth/Users   │
│  - List tables  │
│  - Create table │
└────────┬────────┘
         │
         ▼ (provides WebSocket URL)
┌─────────────────┐
│  Game Service   │  (WebSocket - Port 8001)
│  - Active game  │
│  - Poker logic  │
└────────┬────────┘
         │
    ┌────▼─────┐        ┌──────────┐
    │  Shared  │◄───────┤ Database │
    │  Module  │        │ (SQLite/ │
    └──────────┘        │  Postgres)
                        └──────────┘
```

- **Lobby Service**: FastAPI REST API for table management and authentication
- **Game Service**: FastAPI + WebSocket for real-time gameplay
- **Shared Module**: Common poker logic, models, database models (SQLAlchemy)
- **Database**: SQLite for dev, PostgreSQL-ready for production
- **Frontend**: React 19 + Vite + React Router
- **Communication**: HTTP for lobby/auth, WebSocket for game (with JWT support)

## Quick Start

### Option 1: Docker (Recommended for Production)

The easiest way to run PokerLite is using Docker:

```bash
# Build and run with docker-compose
docker-compose up --build

# Or build and run with Docker directly
docker build -t pokerlite .
docker run -p 8000:8000 pokerlite
```

The application will be available at http://localhost:8000

### Option 2: Local Development (Recommended for Development)

For development with hot-reload on all services:

#### Automated Setup

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

#### Manual Setup

If you prefer to set up manually:

**Prerequisites:**
- Python 3.11 or higher
- Node.js 18 or higher
- npm

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

### Environment Variables

#### Backend (.env in project root)

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

# Future configurations (not yet implemented):
# REDIS_URL=redis://localhost:6379
# LOG_LEVEL=INFO
```

#### Frontend (.env in poker-client/)

```bash
# WebSocket URL for the backend
VITE_WS_URL=ws://localhost:8000
```

Create these files from the examples:
```bash
cp .env.example .env
cp poker-client/.env.example poker-client/.env
```

## API Endpoints

### HTTP Endpoints

**Health & Info:**
- `GET /api/health` - Health check endpoint

**Authentication:**
- `POST /api/auth/register` - Create new user account (returns JWT token)
- `POST /api/auth/login` - Login with username/password (returns JWT token)
- `GET /api/auth/me` - Get current user info (requires authentication)
- `GET /api/auth/stack` - Get user's chip stack (requires authentication)
- `POST /api/auth/add-chips` - Add chips to stack for testing (requires authentication)

**Tables:**
- `GET /api/tables` - List all active tables
- `POST /api/tables` - Create a new table

### WebSocket Endpoints

- `WS /ws/{table_id}` - Connect to a poker table (supports JWT authentication)

## Development

### Project Structure

```
pokerlite/
├── services/
│   ├── shared/            # Shared poker logic & models
│   │   ├── models/        # Player, TableConfig
│   │   ├── poker/         # Poker logic, hand evaluation
│   │   └── setup.py
│   ├── lobby/             # Lobby service (HTTP REST)
│   │   ├── app/
│   │   │   ├── routes/    # Table CRUD endpoints
│   │   │   ├── storage/   # In-memory/PostgreSQL storage
│   │   │   └── main.py
│   │   ├── tests/         # 9 tests
│   │   └── Dockerfile
│   └── game/              # Game service (WebSocket)
│       ├── app/
│       │   ├── core/      # Game logic, poker rules
│       │   ├── routes/    # WebSocket routes
│       │   └── main.py
│       ├── tests/         # 218 tests
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
├── dev-stop.sh            # Stop all services
└── README.md
```

### Running Tests

**Game Service (218 tests):**
```bash
cd services/game
source .venv/bin/activate
pytest tests/ -v
```

**Lobby Service (9 tests):**
```bash
cd services/lobby
source .venv/bin/activate
pytest tests/ -v
```

**Frontend:**
```bash
cd poker-client
npm test
```

**E2E Tests (WebdriverIO):**
```bash
# Make sure all services are running first
./dev-start.sh

# Navigate to E2E test directory
cd e2e-tests

# Install E2E test dependencies (first time only)
npm install

# Run E2E tests (headed mode - watch tests run)
npm run test:e2e

# Run in headless mode (CI/automated)
HEADLESS=true npm run test:e2e

# Run specific test file
npm run test:e2e -- --spec=e2e/specs/basic-gameplay.e2e.js
```

**E2E test features:**
- Real browser automation with Firefox
- Tests complete gameplay flows (join, start hand, betting, showdown)
- **Authentication flow testing** - Registration, login, logout, token validation
- **Deterministic deck shuffling** - Uses seeded RNG for reproducible test scenarios
- Test-only API endpoints for configuration and state verification
- Headed mode by default for debugging, headless for CI

**Total: 260+ tests (unit + integration + auth + E2E) ✅**

### Building for Production

#### Build Frontend Only

```bash
cd poker-client
npm run build
```

The built files will be in `poker-client/dist/`

#### Build Docker Image

```bash
docker build -t pokerlite .
```

## Deployment

### Docker Deployment

1. Build the image:
   ```bash
   docker-compose build
   ```

2. Run the container:
   ```bash
   docker-compose up -d
   ```

3. Check logs:
   ```bash
   docker-compose logs -f
   ```

4. Stop the container:
   ```bash
   docker-compose down
   ```

### Manual Deployment

1. Build the frontend:
   ```bash
   cd poker-client
   npm run build
   ```

2. Copy the built files to `server/static/`:
   ```bash
   mkdir -p server/static
   cp -r poker-client/dist/* server/static/
   ```

3. Run the backend:
   ```bash
   cd server
   source .venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## How to Play

1. Open the application in your browser (http://localhost:5173)
2. **Optional**: Create an account or login to save your chip stack
   - Click "Login / Sign Up" in the lobby
   - Register with a username and password
   - Or continue as guest (chip count won't persist)
3. Browse available tables or create a new one
4. Click "Join Table" to enter a game
5. Wait for at least 2 players to join
6. Click "Start Hand" to begin a new hand
7. Use the action buttons (Check, Call, Raise, Fold) to play

## Roadmap

**Completed Features:**
- [x] PostgreSQL integration for user profiles
- [x] User authentication and authorization (JWT)
- [x] Persistent chip stacks across sessions
- [x] Database migrations (Alembic)

**Future Enhancements:**
- [ ] Game history and hand replay
- [ ] Player statistics and leaderboards
- [ ] Logging and monitoring
- [ ] Tournament mode
- [ ] Chat functionality
- [ ] Mobile-responsive design improvements
- [ ] Email verification
- [ ] Password reset functionality

## Contributing

Contributions are welcome! This is a learning/demonstration project and PRs for new features, bug fixes, or improvements are appreciated.

### Areas for Contribution
- Tournament mode
- Chat functionality
- PostgreSQL integration
- User authentication
- Player statistics and leaderboards
- Mobile responsive improvements
- Performance optimizations

## License

MIT License - see [LICENSE](LICENSE) file for details.

This is free and open source software. You can use it for any purpose, including commercial projects.

## Disclaimer

⚠️ **Educational/Entertainment Project**

This is a learning and demonstration project. Not intended for real money gambling. Use at your own risk.

## Support

For issues and questions, please open an issue on GitHub.
