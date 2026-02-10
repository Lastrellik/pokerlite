"""Tests for WebSocket authentication and error handling."""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi import WebSocket
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import create_access_token, User, PlayerStack, Base, hash_password


class MockWebSocket:
    """Mock WebSocket for testing."""
    def __init__(self):
        self.messages_sent = []
        self.closed = False
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def send_text(self, message):
        self.messages_sent.append(message)

    async def close(self):
        self.closed = True

    async def receive_text(self):
        # Override this in tests
        pass


class TestWebSocketAuthErrors:
    """Test WebSocket authentication error handling."""

    @pytest.mark.asyncio
    async def test_invalid_json_closes_connection(self):
        """Test that invalid JSON in join message closes connection."""
        from app.routes.ws import ws_endpoint
        from app.core.tables import get_table

        # Create a table
        table_id = "test_table"
        table = get_table(table_id)

        # Mock WebSocket that returns invalid JSON
        ws = MockWebSocket()
        ws.receive_text = AsyncMock(return_value="not valid json {")

        await ws_endpoint(ws, table_id)

        assert ws.accepted
        assert ws.closed

    @pytest.mark.asyncio
    async def test_missing_type_closes_connection(self):
        """Test that missing 'type' field closes connection."""
        from app.routes.ws import ws_endpoint
        from app.core.tables import get_table

        table_id = "test_table"
        table = get_table(table_id)

        ws = MockWebSocket()
        ws.receive_text = AsyncMock(return_value=json.dumps({"name": "Alice"}))

        await ws_endpoint(ws, table_id)

        assert ws.accepted
        assert ws.closed
        # Should have sent error message
        assert any("first message must be type=join" in msg for msg in ws.messages_sent)

    @pytest.mark.asyncio
    async def test_invalid_token_closes_connection(self):
        """Test that invalid authentication token closes connection."""
        from app.routes.ws import ws_endpoint
        from app.core.tables import get_table

        table_id = "test_table"
        table = get_table(table_id)

        ws = MockWebSocket()
        join_msg = json.dumps({
            "type": "join",
            "name": "Alice",
            "token": "invalid_token_123"
        })
        ws.receive_text = AsyncMock(return_value=join_msg)

        await ws_endpoint(ws, table_id)

        assert ws.accepted
        assert ws.closed
        # Should have sent auth error
        assert any("Invalid authentication token" in msg for msg in ws.messages_sent)

    @pytest.mark.asyncio
    async def test_expired_token_closes_connection(self, test_user):
        """Test that expired token is rejected."""
        from app.routes.ws import ws_endpoint
        from app.core.tables import get_table
        from datetime import timedelta

        table_id = "test_table"
        table = get_table(table_id)

        # Create an expired token (negative expiration)
        expired_token = create_access_token(
            data={"sub": test_user.username},
            expires_delta=timedelta(minutes=-30)  # Already expired
        )

        ws = MockWebSocket()
        join_msg = json.dumps({
            "type": "join",
            "name": "Alice",
            "token": expired_token
        })
        ws.receive_text = AsyncMock(return_value=join_msg)

        await ws_endpoint(ws, table_id)

        assert ws.accepted
        assert ws.closed
        # Should reject expired token
        assert any("Invalid authentication token" in msg for msg in ws.messages_sent)

    @pytest.mark.asyncio
    async def test_valid_token_accepts_connection(self, test_user):
        """Test that valid token allows connection."""
        from app.routes.ws import ws_endpoint
        from app.core.tables import get_table

        table_id = "test_table"
        table = get_table(table_id)

        # Create valid token
        valid_token = create_access_token(data={"sub": test_user.username})

        ws = MockWebSocket()
        join_msg = json.dumps({
            "type": "join",
            "name": test_user.username,
            "token": valid_token
        })

        messages_to_return = [join_msg]
        call_count = [0]

        async def mock_receive():
            if call_count[0] < len(messages_to_return):
                result = messages_to_return[call_count[0]]
                call_count[0] += 1
                return result
            # Simulate disconnect after first message
            from fastapi import WebSocketDisconnect
            raise WebSocketDisconnect()

        ws.receive_text = mock_receive

        await ws_endpoint(ws, table_id)

        assert ws.accepted
        # Should have sent welcome message
        assert any("welcome" in msg for msg in ws.messages_sent)

    @pytest.mark.asyncio
    async def test_guest_connection_without_token(self):
        """Test that guest connections work without token."""
        from app.routes.ws import ws_endpoint
        from app.core.tables import get_table

        table_id = "test_table"
        table = get_table(table_id)

        ws = MockWebSocket()
        join_msg = json.dumps({
            "type": "join",
            "name": "Guest123"
        })

        messages_to_return = [join_msg]
        call_count = [0]

        async def mock_receive():
            if call_count[0] < len(messages_to_return):
                result = messages_to_return[call_count[0]]
                call_count[0] += 1
                return result
            from fastapi import WebSocketDisconnect
            raise WebSocketDisconnect()

        ws.receive_text = mock_receive

        await ws_endpoint(ws, table_id)

        assert ws.accepted
        # Should have sent welcome message
        assert any("welcome" in msg for msg in ws.messages_sent)


# Database setup for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ws_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)

    # Monkey-patch get_db
    import db as db_module
    from app.core import auth as auth_module

    original_get_db = db_module.get_db
    db_module.get_db = override_get_db
    auth_module.get_db = override_get_db

    yield

    # Restore original
    db_module.get_db = original_get_db
    auth_module.get_db = original_get_db
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    """Create a test user with stack in database."""
    db = next(override_get_db())

    user = User(
        username="testuser",
        password_hash=hash_password("password123"),
        email="test@example.com",
        avatar_id="chips"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    stack = PlayerStack(user_id=user.id, stack=1500)
    db.add(stack)
    db.commit()

    # Access attributes before closing to load them into memory
    user_id = user.id
    username = user.username
    email = user.email

    db.close()

    # Create a simple object with the needed attributes
    class TestUser:
        def __init__(self, id, username, email):
            self.id = id
            self.username = username
            self.email = email

    return TestUser(user_id, username, email)
