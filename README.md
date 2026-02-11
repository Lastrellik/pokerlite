# PokerLite 🎰

A real-time multiplayer Texas Hold'em poker application built with FastAPI (Python) and React.

> **Note**: This project was developed with AI assistance using Claude Code, demonstrating modern AI-augmented development workflows. See commit history for co-authorship details.

## ✨ Features

**Gameplay**
- Real-time multiplayer Texas Hold'em (2-8 players)
- Advanced side pot system with multi-way all-ins
- Spectator mode and waitlist system
- Turn timeout with auto-fold/check
- All-in runout with card reveal animations

**Authentication & Persistence**
- JWT-based user accounts with secure password hashing
- Persistent chip stacks across sessions
- Guest mode for quick play
- SQLite for development, PostgreSQL-ready for production

**Technical**
- Microservices architecture (lobby + game services)
- WebSocket for real-time game updates
- Database integration with SQLAlchemy ORM
- Comprehensive test coverage (390+ tests)
- Docker support for easy deployment

## 🚀 Quick Start

### Option 1: Automated (Recommended for Development)

```bash
# Start all services with one command
./dev-start.sh

# Stop all services
./dev-stop.sh
```

**Access the app:**
- Frontend: http://localhost:5173
- Lobby API: http://localhost:8000
- Game WebSocket: ws://localhost:8001

### Option 2: Docker (Recommended for Production)

```bash
# Build and run with docker-compose
docker-compose up --build

# The application will be available at http://localhost:8000
```

## 📖 Documentation

- **[Development Guide](DEVELOPMENT.md)** - Setup, tests, project structure
- **[API Documentation](API.md)** - HTTP endpoints, WebSocket protocol, authentication
- **[Deployment Guide](DEPLOYMENT.md)** - Docker deployment, production setup, security

## 🎮 How to Play

1. Open http://localhost:5173 in your browser
2. **Optional**: Create an account or login to save your chip stack
   - Click "Login / Sign Up" in the lobby
   - Or continue as guest (chip count won't persist)
3. Browse available tables or create a new one
4. Click "Join Table" to enter a game
5. Wait for at least 2 players, then click "Start Hand"
6. Use action buttons (Check, Call, Raise, Fold) to play

## 🏗️ Architecture

```
┌─────────────────┐
│  Lobby Service  │  (HTTP REST - Port 8000)
│  - Auth/Users   │  - FastAPI
│  - Tables CRUD  │  - SQLAlchemy + PostgreSQL/SQLite
└────────┬────────┘
         │
         ▼ (provides WebSocket URL)
┌─────────────────┐
│  Game Service   │  (WebSocket - Port 8001)
│  - Live Games   │  - FastAPI WebSockets
│  - Poker Logic  │  - Event-driven state updates
└────────┬────────┘
         │
    ┌────▼─────┐
    │  Shared  │  - Poker hand evaluation
    │  Module  │  - Game state models
    └──────────┘  - Database models
```

**Frontend:** React 19 + Vite + React Router
**Communication:** HTTP for lobby/auth, WebSocket for gameplay with JWT support

## ✅ Testing

All 390+ tests passing:
- **Backend**: 261 tests (pytest)
- **Frontend**: 127 tests (vitest)
- **E2E**: 3 tests (WebdriverIO)

```bash
# Run all tests
cd services/game && pytest tests/    # Backend (game)
cd services/lobby && pytest tests/   # Backend (lobby)
cd poker-client && npm test          # Frontend
cd e2e-tests && npm run test:e2e     # E2E (requires services running)
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed testing instructions.

## 🗺️ Roadmap

**Completed:**
- [x] User authentication and authorization (JWT)
- [x] Persistent chip stacks across sessions
- [x] Database integration with migrations
- [x] Lobby-based authentication

**Planned:**
- [ ] Password reset functionality
- [ ] Email verification
- [ ] Rate limiting and security hardening
- [ ] Game history and hand replay
- [ ] Player statistics and leaderboards
- [ ] Tournament mode
- [ ] Chat functionality
- [ ] Mobile-responsive design

## 🤝 Contributing

Contributions welcome! This is a learning/demonstration project.

**Areas for contribution:**
- Security improvements (rate limiting, password validation, CAPTCHA)
- Tournament mode
- Chat functionality
- Player statistics
- Mobile responsive design
- Performance optimizations

## ⚠️ Disclaimer

**Educational/Entertainment Project**

This is a learning and demonstration project. Not intended for real money gambling. Use at your own risk.

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

This is free and open source software. You can use it for any purpose, including commercial projects.

## 💬 Support

For issues and questions, please open an issue on GitHub.
