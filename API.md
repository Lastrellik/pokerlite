# API Documentation

PokerLite uses a microservices architecture with HTTP REST for lobby operations and WebSocket for real-time gameplay.

## Architecture Overview

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

## HTTP Endpoints

Base URL: `http://localhost:8000`

### Health & Info

#### Get Health Status
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### Authentication

#### Register New User
```http
POST /api/auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "player1",
  "password": "secure_password",
  "email": "player1@example.com",  // optional
  "avatar_id": "chips"              // optional, default: "chips"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "player1",
    "email": "player1@example.com",
    "avatar_id": "chips"
  }
}
```

**Errors:**
- `400 Bad Request` - Username already registered
- `400 Bad Request` - Email already registered
- `422 Unprocessable Entity` - Validation error (username too short, password too short)

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
```
username=player1&password=secure_password
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "player1",
    "email": "player1@example.com",
    "avatar_id": "chips"
  }
}
```

**Errors:**
- `401 Unauthorized` - Incorrect username or password

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "player1",
  "email": "player1@example.com",
  "avatar_id": "chips"
}
```

**Errors:**
- `401 Unauthorized` - Invalid or expired token

#### Get User Chip Stack
```http
GET /api/auth/stack
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "stack": 5000,
  "user_id": 1,
  "username": "player1"
}
```

**Errors:**
- `401 Unauthorized` - Invalid token

#### Add Chips (Testing Only)
```http
POST /api/auth/add-chips
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "amount": 1000  // 1-100,000
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "new_stack": 6000,
  "added": 1000
}
```

### Tables

#### List All Tables
```http
GET /api/tables
```

**Response (200 OK):**
```json
[
  {
    "table_id": "abc123",
    "name": "High Stakes",
    "small_blind": 5,
    "big_blind": 10,
    "max_players": 8,
    "turn_timeout_seconds": 30
  }
]
```

#### Create Table
```http
POST /api/tables
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "My Poker Table",
  "small_blind": 5,
  "big_blind": 10,
  "max_players": 8,           // 2-8
  "turn_timeout_seconds": 30  // optional, default: 30
}
```

**Response (201 Created):**
```json
{
  "table_id": "abc123",
  "name": "My Poker Table",
  "small_blind": 5,
  "big_blind": 10,
  "max_players": 8,
  "turn_timeout_seconds": 30
}
```

**Errors:**
- `422 Unprocessable Entity` - Validation error

## WebSocket Protocol

Base URL: `ws://localhost:8001`

### Connect to Table
```
ws://localhost:8001/ws/{table_id}
```

### Client → Server Messages

#### Join Table (Guest)
```json
{
  "type": "join",
  "name": "PlayerName",
  "pid": null  // or previous player ID for reconnection
}
```

#### Join Table (Authenticated)
```json
{
  "type": "join",
  "name": "PlayerName",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Start New Hand
```json
{
  "type": "start_hand"
}
```

#### Player Action
```json
{
  "type": "action",
  "action": "raise",  // fold, check, call, raise, all_in
  "amount": 50        // required for raise
}
```

### Server → Client Messages

#### Welcome Message
```json
{
  "type": "welcome",
  "pid": "player-uuid",
  "message": "Connected to table"
}
```

#### Game State Update
```json
{
  "type": "state",
  "state": {
    "players": [...],
    "board": ["Ah", "Kd", "Qc"],
    "pot": 150,
    "current_turn": "player-uuid",
    "street": "flop",
    // ... full game state
  }
}
```

#### Error Message
```json
{
  "type": "error",
  "message": "Error description"
}
```

#### Log Message
```json
{
  "type": "log",
  "message": "PlayerName bets 50"
}
```

## Authentication Flow

1. **Register/Login** → Receive JWT token
2. **Store token** in localStorage
3. **Include token** in WebSocket join message or HTTP Authorization header
4. **Server validates** token and loads user's chip stack
5. **Token expires** after 60 minutes (configurable)
6. **Client detects** expiration and prompts re-login

### Token Structure

JWT tokens contain:
- `sub` (subject) - username
- `exp` (expiration) - Unix timestamp
- Signed with HS256 algorithm

### Security Notes

⚠️ **Current Implementation (Development)**
- Passwords hashed with bcrypt
- JWT tokens with expiration
- CORS enabled for development origins

⚠️ **Production Requirements** (Not Yet Implemented)
- Rate limiting on auth endpoints
- Username enumeration prevention
- Password strength requirements
- Email verification
- Password reset flow
- CAPTCHA for registration
- HTTPS only
- Secure token storage
