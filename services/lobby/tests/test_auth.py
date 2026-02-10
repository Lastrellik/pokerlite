"""Tests for authentication routes."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from db import Base, get_db, User, PlayerStack

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


class TestRegister:
    """Test user registration."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123", "email": "test@example.com"}
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
        assert "password" not in data["user"]

    def test_register_creates_initial_stack(self, client):
        """Test that registration creates initial chip stack."""
        client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"}
        )

        # Check database directly
        db = next(override_get_db())
        user = db.query(User).filter(User.username == "testuser").first()
        assert user is not None

        stack = db.query(PlayerStack).filter(PlayerStack.user_id == user.id).first()
        assert stack is not None
        assert stack.stack == 1000  # Default starting stack

    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username."""
        client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"}
        )

        response = client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "different"}
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email."""
        client.post(
            "/api/auth/register",
            json={"username": "user1", "password": "password123", "email": "test@example.com"}
        )

        response = client.post(
            "/api/auth/register",
            json={"username": "user2", "password": "password123", "email": "test@example.com"}
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_without_email(self, client):
        """Test registration without email (optional field)."""
        response = client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["email"] is None

    def test_register_custom_avatar(self, client):
        """Test registration with custom avatar selection."""
        response = client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123", "avatar_id": "ace"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["avatar_id"] == "ace"

    def test_register_validation_short_username(self, client):
        """Test registration with username too short."""
        response = client.post(
            "/api/auth/register",
            json={"username": "ab", "password": "password123"}
        )

        assert response.status_code == 422  # Validation error

    def test_register_validation_short_password(self, client):
        """Test registration with password too short."""
        response = client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "12345"}
        )

        assert response.status_code == 422  # Validation error


class TestLogin:
    """Test user login."""

    def test_login_success(self, client):
        """Test successful login."""
        # Register user first
        client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"}
        )

        # Login
        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "password123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"

    def test_login_updates_last_login(self, client):
        """Test that login updates last_login timestamp."""
        # Register user
        client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"}
        )

        # Check last_login is None initially
        db = next(override_get_db())
        user = db.query(User).filter(User.username == "testuser").first()
        assert user.last_login is None

        # Login
        client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "password123"}
        )

        # Check last_login is set
        db = next(override_get_db())
        user = db.query(User).filter(User.username == "testuser").first()
        assert user.last_login is not None

    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123"}
        )

        response = client.post(
            "/api/auth/login",
            data={"username": "testuser", "password": "wrongpassword"}
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent username."""
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent", "password": "password123"}
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()


class TestGetCurrentUser:
    """Test getting current user info."""

    def test_get_current_user_success(self, client):
        """Test getting current user with valid token."""
        # Register and get token
        reg_response = client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "password123", "email": "test@example.com"}
        )
        token = reg_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_get_current_user_expired_token(self, client):
        """Test getting current user with expired token."""
        # This would require mocking time or using a very short expiration
        # For now, just test that a malformed token fails
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired.token"}
        )

        assert response.status_code == 401
