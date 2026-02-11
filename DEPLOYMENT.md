# Deployment Guide

This guide covers production deployment options for PokerLite.

## Docker Deployment (Recommended)

The easiest way to deploy PokerLite is using Docker Compose.

### Quick Start

```bash
# Build and run all services
docker-compose up --build

# Run in detached mode (background)
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop all services
docker-compose down
```

The application will be available at http://localhost:8000

### Docker Build Only

```bash
# Build the Docker image
docker build -t pokerlite .

# Run the container
docker run -p 8000:8000 pokerlite
```

## Manual Deployment

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL (recommended for production)
- Reverse proxy (nginx/Apache) for HTTPS
- Process manager (systemd/supervisord)

### Step 1: Build Frontend

```bash
cd poker-client
npm install
npm run build
```

This creates production-optimized static files in `poker-client/dist/`

### Step 2: Set Up Backend Services

**Lobby Service:**

```bash
cd services/lobby
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run with gunicorn for production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Game Service:**

```bash
cd services/game
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ../shared

# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

### Step 3: Serve Frontend

Option 1 - Use nginx to serve static files:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Serve frontend
    location / {
        root /path/to/poker-client/dist;
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to lobby service
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Proxy WebSocket to game service
    location /ws/ {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

Option 2 - Copy frontend to backend static folder:

```bash
mkdir -p services/lobby/static
cp -r poker-client/dist/* services/lobby/static/
```

## Production Configuration

### Environment Variables

**Critical settings for production:**

```bash
# Security
SECRET_KEY=<generate-strong-random-key>  # Use: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/pokerlite

# Server
HOST=0.0.0.0
PORT=8000

# CORS - Set to your actual domain(s)
CORS_ORIGINS=https://your-domain.com

# Optional
LOG_LEVEL=INFO
```

### Database Setup (PostgreSQL)

```bash
# Create database
createdb pokerlite

# Run migrations (if using Alembic)
cd services/shared
alembic upgrade head
```

The database schema will be created automatically on first run if using SQLAlchemy.

### Generating Secure Secret Key

```bash
# Generate a secure random key
openssl rand -hex 32
```

Add this to your `.env` file as `SECRET_KEY`.

## Process Management

### Using systemd (Linux)

**Lobby service** (`/etc/systemd/system/pokerlite-lobby.service`):

```ini
[Unit]
Description=PokerLite Lobby Service
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/pokerlite/services/lobby
Environment="PATH=/opt/pokerlite/services/lobby/.venv/bin"
ExecStart=/opt/pokerlite/services/lobby/.venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Game service** (`/etc/systemd/system/pokerlite-game.service`):

```ini
[Unit]
Description=PokerLite Game Service
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/pokerlite/services/game
Environment="PATH=/opt/pokerlite/services/game/.venv/bin"
ExecStart=/opt/pokerlite/services/game/.venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl enable pokerlite-lobby pokerlite-game
sudo systemctl start pokerlite-lobby pokerlite-game
sudo systemctl status pokerlite-lobby pokerlite-game
```

## Security Checklist

Before deploying to production:

- [ ] Generate and set a strong `SECRET_KEY`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS (use Let's Encrypt)
- [ ] Set CORS to your actual domain(s)
- [ ] Add rate limiting to auth endpoints
- [ ] Implement password strength requirements
- [ ] Add email verification
- [ ] Set up monitoring and logging
- [ ] Configure firewall rules
- [ ] Regular database backups
- [ ] Keep dependencies updated

## Monitoring

### Health Checks

```bash
# Check lobby service
curl http://localhost:8000/api/health

# Check if services are running
systemctl status pokerlite-lobby
systemctl status pokerlite-game
```

### Logs

```bash
# View service logs
journalctl -u pokerlite-lobby -f
journalctl -u pokerlite-game -f

# Docker logs
docker-compose logs -f lobby
docker-compose logs -f game
```

## Scaling Considerations

- **Horizontal scaling**: Run multiple instances behind a load balancer
- **Database**: Use connection pooling, read replicas for heavy traffic
- **WebSocket**: Sticky sessions required for game service
- **Caching**: Consider Redis for session management and table state
- **CDN**: Serve static frontend assets from CDN

## Troubleshooting

### Services won't start

```bash
# Check logs
journalctl -u pokerlite-lobby -n 50
journalctl -u pokerlite-game -n 50

# Check if ports are in use
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :8001
```

### Database connection issues

```bash
# Test PostgreSQL connection
psql -U user -d pokerlite -c "SELECT 1;"

# Check DATABASE_URL format
echo $DATABASE_URL
```

### WebSocket connection fails

- Ensure nginx is configured for WebSocket upgrade
- Check CORS settings
- Verify game service is running
- Test WebSocket connection: `wscat -c ws://localhost:8001/ws/test-table`
