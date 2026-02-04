# PokerLite 🎰

A real-time multiplayer poker application built with FastAPI (Python) and React.

> **Note**: This project was developed with AI assistance using Claude Code, demonstrating modern AI-augmented development workflows. See commit history for co-authorship details.

## Features

### Lobby System
- **Table browser** - Browse and join active tables
- **Create tables** - Customizable blinds, player limits, and turn timeouts
- **Auto-refresh** - Table list updates every 5 seconds

### Gameplay
- Real-time multiplayer Texas Hold'em poker
- WebSocket-based communication for instant updates
- Clean, modern React UI with elliptical table layout
- Up to 8 players per table with automatic seat assignment
- **Side pot handling** - Correctly manages multiple side pots with different stack sizes
- **Detailed game log** - Shows all actions, street changes, and side pot breakdowns
- Spectator mode for watching games in progress
- Waitlist system with automatic promotion when seats open
- Turn timeout with auto-fold/check
- All-in runout with card-by-card reveal animations
- **Clear all-in indicators** - Shows when calling is an all-in action

### Technical
- Microservices architecture (lobby + game services)
- Shared poker logic module
- Comprehensive test coverage (201 tests)
- Docker support for easy deployment

## Architecture

```
┌─────────────────┐
│  Lobby Service  │  (HTTP REST - Port 8000)
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
    ┌────▼─────┐
    │  Shared  │  (Common poker logic)
    └──────────┘
```

- **Lobby Service**: FastAPI REST API for table management
- **Game Service**: FastAPI + WebSocket for real-time gameplay
- **Shared Module**: Common poker logic, models, and utilities
- **Frontend**: React 19 + Vite + React Router
- **Communication**: HTTP for lobby, WebSocket for game

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

# Future configurations (not yet implemented):
# DATABASE_URL=postgresql://user:password@localhost:5432/pokerlite
# REDIS_URL=redis://localhost:6379
# SECRET_KEY=your-secret-key
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

- `GET /api/health` - Health check endpoint

### WebSocket Endpoints

- `WS /ws/{table_id}` - Connect to a poker table

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
│       ├── tests/         # 192 tests
│       └── Dockerfile
├── poker-client/          # React frontend
│   ├── src/
│   │   ├── components/    # Lobby, GamePage, PokerTable
│   │   ├── hooks/         # usePokerGame, useLobby
│   │   └── App.jsx        # React Router setup
│   └── package.json
├── docker-compose.yml     # Multi-service orchestration
├── dev-start.sh           # Start all services locally
├── dev-stop.sh            # Stop all services
└── README.md
```

### Running Tests

**Game Service (192 tests):**
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

**Total: 201 tests, all passing ✅**

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

1. Open the application in your browser
2. Enter your player name and table ID
3. Click "Connect" to join a table
4. Wait for at least 2 players to join
5. Click "Start Hand" to begin a new hand
6. Use the action buttons (Check, Call, Raise, Fold) to play

## Roadmap

Future enhancements planned:

- [ ] PostgreSQL integration for user profiles and game history
- [ ] User authentication and authorization
- [ ] Persistent game state
- [ ] Player statistics and leaderboards
- [ ] Logging and monitoring
- [ ] Tournament mode
- [ ] Chat functionality
- [ ] Mobile-responsive design improvements

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
