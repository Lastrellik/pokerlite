"""Tests for admin routes and admin bootstrap logic."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.main import app
from db import Base, get_db, User, PlayerStack

# Create test database (separate file from test_auth.db to avoid conflicts)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin.db"
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
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def register_and_login(client, username="testuser", password="password123"):
    """Helper: register a user and return their token."""
    client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )
    response = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    return response.json()["access_token"]


def make_admin(username):
    """Helper: directly set is_admin=True in DB for a user."""
    db = next(override_get_db())
    user = db.query(User).filter(User.username == username).first()
    user.is_admin = True
    db.commit()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Admin bootstrap (login auto-promote)
# ---------------------------------------------------------------------------

class TestAdminBootstrap:
    """Test ADMIN_USERNAME auto-promotion on login."""

    def test_login_returns_is_admin_false_for_normal_user(self, client):
        """Regular users get is_admin=False in the login response."""
        client.post("/api/auth/register", json={"username": "alice", "password": "password123"})
        response = client.post("/api/auth/login", data={"username": "alice", "password": "password123"})
        assert response.status_code == 200
        assert response.json()["is_admin"] is False

    def test_login_promotes_admin_username_on_first_login(self, client):
        """User matching ADMIN_USERNAME is auto-promoted on login."""
        client.post("/api/auth/register", json={"username": "superadmin", "password": "password123"})

        with patch.dict(os.environ, {"ADMIN_USERNAME": "superadmin"}):
            response = client.post(
                "/api/auth/login",
                data={"username": "superadmin", "password": "password123"},
            )

        assert response.status_code == 200
        assert response.json()["is_admin"] is True

        # Verify DB was updated
        db = next(override_get_db())
        user = db.query(User).filter(User.username == "superadmin").first()
        assert user.is_admin is True

    def test_login_does_not_promote_other_users(self, client):
        """Only the exact ADMIN_USERNAME match is promoted."""
        client.post("/api/auth/register", json={"username": "bob", "password": "password123"})
        client.post("/api/auth/register", json={"username": "superadmin", "password": "password123"})

        with patch.dict(os.environ, {"ADMIN_USERNAME": "superadmin"}):
            response = client.post(
                "/api/auth/login",
                data={"username": "bob", "password": "password123"},
            )

        assert response.json()["is_admin"] is False

    def test_login_with_no_admin_username_env_var(self, client):
        """When ADMIN_USERNAME is unset, no auto-promotion occurs."""
        client.post("/api/auth/register", json={"username": "alice", "password": "password123"})

        env = {k: v for k, v in os.environ.items() if k != "ADMIN_USERNAME"}
        with patch.dict(os.environ, env, clear=True):
            response = client.post(
                "/api/auth/login",
                data={"username": "alice", "password": "password123"},
            )

        assert response.json()["is_admin"] is False

    def test_register_returns_is_admin_false(self, client):
        """Registration always returns is_admin=False."""
        response = client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "password123"},
        )
        assert response.status_code == 201
        assert response.json()["is_admin"] is False

    def test_login_already_admin_stays_admin(self, client):
        """A user who is already admin keeps is_admin=True on subsequent logins."""
        client.post("/api/auth/register", json={"username": "superadmin", "password": "password123"})
        make_admin("superadmin")

        response = client.post(
            "/api/auth/login",
            data={"username": "superadmin", "password": "password123"},
        )
        assert response.json()["is_admin"] is True


# ---------------------------------------------------------------------------
# GET /api/admin/users
# ---------------------------------------------------------------------------

class TestListUsers:
    """Test GET /api/admin/users."""

    def test_list_users_requires_auth(self, client):
        """Unauthenticated request is rejected with 401."""
        response = client.get("/api/admin/users")
        assert response.status_code == 401

    def test_list_users_requires_admin(self, client):
        """Non-admin user receives 403."""
        token = register_and_login(client, "regular", "password123")
        response = client.get("/api/admin/users", headers=auth_headers(token))
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    def test_list_users_returns_all_users(self, client):
        """Admin gets a list of all users."""
        register_and_login(client, "alice", "password123")
        register_and_login(client, "bob", "password123")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")

        response = client.get("/api/admin/users", headers=auth_headers(admin_token))
        assert response.status_code == 200
        data = response.json()
        usernames = [u["username"] for u in data]
        assert "alice" in usernames
        assert "bob" in usernames
        assert "admin" in usernames

    def test_list_users_includes_stack(self, client):
        """Each user entry includes their chip stack."""
        register_and_login(client, "alice", "password123")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")

        response = client.get("/api/admin/users", headers=auth_headers(admin_token))
        assert response.status_code == 200
        alice = next(u for u in response.json() if u["username"] == "alice")
        assert alice["stack"] == 1000  # Default starting stack

    def test_list_users_includes_is_admin_flag(self, client):
        """Each user entry includes their is_admin status."""
        register_and_login(client, "regular", "password123")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")

        response = client.get("/api/admin/users", headers=auth_headers(admin_token))
        data = response.json()
        regular = next(u for u in data if u["username"] == "regular")
        admin_user = next(u for u in data if u["username"] == "admin")
        assert regular["is_admin"] is False
        assert admin_user["is_admin"] is True

    def test_list_users_stack_none_when_no_stack_row(self, client):
        """Users without a stack row show stack as None."""
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")

        # Manually create a user without a stack row
        db = next(override_get_db())
        new_user = User(username="nostack", email=None, password_hash="x", avatar_id="chips")
        db.add(new_user)
        db.commit()

        response = client.get("/api/admin/users", headers=auth_headers(admin_token))
        nostack = next(u for u in response.json() if u["username"] == "nostack")
        assert nostack["stack"] is None


# ---------------------------------------------------------------------------
# PATCH /api/admin/users/{id}/stack
# ---------------------------------------------------------------------------

class TestSetStack:
    """Test PATCH /api/admin/users/{user_id}/stack."""

    def _get_target_user_id(self, username="alice"):
        db = next(override_get_db())
        user = db.query(User).filter(User.username == username).first()
        return user.id

    def test_set_stack_requires_admin(self, client):
        """Non-admin receives 403."""
        register_and_login(client, "alice", "password123")
        token = register_and_login(client, "regular", "password123")
        user_id = self._get_target_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/stack",
            json={"stack": 5000},
            headers=auth_headers(token),
        )
        assert response.status_code == 403

    def test_set_stack_updates_existing_stack(self, client):
        """Setting stack on a user with an existing row updates it."""
        register_and_login(client, "alice", "password123")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")
        user_id = self._get_target_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/stack",
            json={"stack": 9999},
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["stack"] == 9999

        # Verify in DB
        db = next(override_get_db())
        stack_row = db.query(PlayerStack).filter(PlayerStack.user_id == user_id).first()
        assert stack_row.stack == 9999

    def test_set_stack_upserts_when_no_stack_row(self, client):
        """Setting stack on a user with no stack row creates one."""
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")

        db = next(override_get_db())
        new_user = User(username="nostack", email=None, password_hash="x", avatar_id="chips")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user_id = new_user.id

        response = client.patch(
            f"/api/admin/users/{user_id}/stack",
            json={"stack": 500},
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["stack"] == 500

    def test_set_stack_to_zero(self, client):
        """Stack can be set to zero."""
        register_and_login(client, "alice", "password123")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")
        user_id = self._get_target_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/stack",
            json={"stack": 0},
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["stack"] == 0

    def test_set_stack_max_allowed(self, client):
        """Stack can be set to the maximum allowed value (10,000,000)."""
        register_and_login(client, "alice", "password123")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")
        user_id = self._get_target_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/stack",
            json={"stack": 10_000_000},
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 200

    def test_set_stack_rejects_negative(self, client):
        """Negative stack values are rejected with 422."""
        register_and_login(client, "alice", "password123")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")
        user_id = self._get_target_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/stack",
            json={"stack": -1},
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 422

    def test_set_stack_rejects_over_max(self, client):
        """Values above 10,000,000 are rejected with 422."""
        register_and_login(client, "alice", "password123")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")
        user_id = self._get_target_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/stack",
            json={"stack": 10_000_001},
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 422

    def test_set_stack_unknown_user_returns_404(self, client):
        """Non-existent user ID returns 404."""
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")

        response = client.patch(
            "/api/admin/users/99999/stack",
            json={"stack": 1000},
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/admin/users/{id}/promote
# ---------------------------------------------------------------------------

class TestPromoteUser:
    """Test PATCH /api/admin/users/{user_id}/promote."""

    def _get_user_id(self, username):
        db = next(override_get_db())
        user = db.query(User).filter(User.username == username).first()
        return user.id

    def test_promote_requires_admin(self, client):
        """Non-admin receives 403."""
        register_and_login(client, "alice", "password123")
        token = register_and_login(client, "regular", "password123")
        user_id = self._get_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/promote",
            headers=auth_headers(token),
        )
        assert response.status_code == 403

    def test_promote_sets_is_admin_true(self, client):
        """Promoting a user sets is_admin=True in DB."""
        register_and_login(client, "alice", "password123")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")
        user_id = self._get_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/promote",
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["is_admin"] is True

        db = next(override_get_db())
        alice = db.query(User).filter(User.username == "alice").first()
        assert alice.is_admin is True

    def test_promote_already_admin_is_idempotent(self, client):
        """Promoting an already-admin user is idempotent."""
        register_and_login(client, "alice", "password123")
        make_admin("alice")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")
        user_id = self._get_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/promote",
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["is_admin"] is True

    def test_promote_unknown_user_returns_404(self, client):
        """Non-existent user ID returns 404."""
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")

        response = client.patch(
            "/api/admin/users/99999/promote",
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/admin/users/{id}/demote
# ---------------------------------------------------------------------------

class TestDemoteUser:
    """Test PATCH /api/admin/users/{user_id}/demote."""

    def _get_user_id(self, username):
        db = next(override_get_db())
        user = db.query(User).filter(User.username == username).first()
        return user.id

    def test_demote_requires_admin(self, client):
        """Non-admin receives 403."""
        register_and_login(client, "alice", "password123")
        token = register_and_login(client, "regular", "password123")
        user_id = self._get_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/demote",
            headers=auth_headers(token),
        )
        assert response.status_code == 403

    def test_demote_sets_is_admin_false(self, client):
        """Demoting an admin user sets is_admin=False in DB."""
        register_and_login(client, "alice", "password123")
        make_admin("alice")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")
        user_id = self._get_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/demote",
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["is_admin"] is False

        db = next(override_get_db())
        alice = db.query(User).filter(User.username == "alice").first()
        assert alice.is_admin is False

    def test_demote_self_returns_400(self, client):
        """Admin cannot demote themselves."""
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")
        admin_id = self._get_user_id("admin")

        response = client.patch(
            f"/api/admin/users/{admin_id}/demote",
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 400
        assert "demote yourself" in response.json()["detail"].lower()

    def test_demote_already_non_admin_is_idempotent(self, client):
        """Demoting a non-admin user is idempotent."""
        register_and_login(client, "alice", "password123")  # not admin
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")
        user_id = self._get_user_id("alice")

        response = client.patch(
            f"/api/admin/users/{user_id}/demote",
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["is_admin"] is False

    def test_demote_unknown_user_returns_404(self, client):
        """Non-existent user ID returns 404."""
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")

        response = client.patch(
            "/api/admin/users/99999/demote",
            headers=auth_headers(admin_token),
        )
        assert response.status_code == 404

    def test_promote_then_demote_round_trip(self, client):
        """Promote then demote returns user to non-admin state."""
        register_and_login(client, "alice", "password123")
        admin_token = register_and_login(client, "admin", "password123")
        make_admin("admin")
        user_id = self._get_user_id("alice")

        client.patch(f"/api/admin/users/{user_id}/promote", headers=auth_headers(admin_token))
        response = client.patch(f"/api/admin/users/{user_id}/demote", headers=auth_headers(admin_token))

        assert response.status_code == 200
        assert response.json()["is_admin"] is False
