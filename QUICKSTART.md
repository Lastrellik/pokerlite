# PokerLite Quick Start Guide

## For Local Development (Best for coding)

```bash
# First time setup
./dev-setup.sh

# Start both servers (run this every time)
./dev-start.sh
```

Then open http://localhost:5173 in your browser.

Press Ctrl+C to stop both servers.

## For Docker (Best for testing/deployment)

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# Stop
docker-compose down
```

Then open http://localhost:8000 in your browser.

## What Changed

### Backend Changes:
- ✅ Removed old HTML test UI
- ✅ Added CORS middleware for local development
- ✅ Added static file serving for production React build
- ✅ Changed health endpoint to `/api/health`
- ✅ Environment-based configuration

### Frontend Changes:
- ✅ WebSocket URL now configurable via environment variable
- ✅ Auto-detects correct WebSocket protocol in production (ws/wss)
- ✅ Falls back to current domain if not configured

### New Files:
- ✅ `Dockerfile` - Multi-stage build (React + Python)
- ✅ `docker-compose.yml` - Easy Docker orchestration
- ✅ `.env.example` - Backend configuration template
- ✅ `poker-client/.env.example` - Frontend configuration template
- ✅ `dev-setup.sh` - Automated local development setup
- ✅ `dev-start.sh` - Start both servers with one command
- ✅ `.gitignore` - Ignore build artifacts and secrets
- ✅ `.dockerignore` - Optimize Docker builds
- ✅ `README.md` - Comprehensive documentation

## Common Commands

### Local Development

```bash
# Backend only
cd server
source .venv/bin/activate
uvicorn app.main:app --reload

# Frontend only
cd poker-client
npm run dev

# Run tests
cd server
python test_game.py
```

### Docker

```bash
# Build
docker-compose build

# Run
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up
```

## Troubleshooting

### "Connection refused" on frontend

Make sure the backend is running on port 8000:
```bash
# Check if backend is running
curl http://localhost:8000/api/health
```

### Frontend can't connect to WebSocket

1. Check that `poker-client/.env` exists with `VITE_WS_URL=ws://localhost:8000`
2. Restart the Vite dev server after changing .env files
3. Check browser console for errors

### Docker build fails

1. Make sure Docker is running
2. Try clearing Docker cache: `docker system prune -a`
3. Check that both `server/requirements.txt` and `poker-client/package.json` exist

### Scripts won't run

Make them executable:
```bash
chmod +x dev-setup.sh dev-start.sh
```

## Next Steps for Future Development

The application is now ready to add:

1. **PostgreSQL** - Uncomment postgres service in `docker-compose.yml`
2. **Redis** - Uncomment redis service in `docker-compose.yml`
3. **Authentication** - Add JWT middleware to backend
4. **Logging** - Configure Python logging to file
5. **User Profiles** - Create database models and migrations

All the configuration placeholders are already in `.env.example`!
