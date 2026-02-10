"""Tests for authentication integration in game service."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.auth import validate_token_and_load_user, update_user_stack
from db import Base, User, PlayerStack, hash_password, create_access_token

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_game_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override get_db for testing
original_get_db = None


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

    # Monkey-patch get_db in both db module and auth module
    import db as db_module
    from app.core import auth as auth_module

    global original_get_db
    original_get_db = db_module.get_db
    db_module.get_db = override_get_db
    auth_module.get_db = override_get_db  # Patch where auth imported it

    yield

    # Restore original
    db_module.get_db = original_get_db
    auth_module.get_db = original_get_db
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    """Create a test user with stack."""
    db = next(override_get_db())

    user = User(
        username="testplayer",
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


class TestValidateTokenAndLoadUser:
    """Test token validation and user loading."""

    def test_valid_token_loads_user_and_stack(self, test_user):
        """Test that valid token loads user with their stack."""
        token = create_access_token(data={"sub": test_user.username})

        result = validate_token_and_load_user(token)

        assert result is not None
        user, stack = result
        assert user.username == "testplayer"
        assert user.email == "test@example.com"
        assert stack == 1500

    def test_invalid_token_returns_none(self):
        """Test that invalid token returns None."""
        result = validate_token_and_load_user("invalid_token_123")
        assert result is None

    def test_token_with_nonexistent_user_returns_none(self):
        """Test that token for non-existent user returns None."""
        token = create_access_token(data={"sub": "nonexistent_user"})

        result = validate_token_and_load_user(token)
        assert result is None

    def test_token_without_username_returns_none(self):
        """Test that token without username (sub) returns None."""
        token = create_access_token(data={"user_id": 123})  # Wrong field

        result = validate_token_and_load_user(token)
        assert result is None

    def test_creates_default_stack_if_missing(self, test_user):
        """Test that default stack is created if user has none."""
        # Delete the user's stack
        db = next(override_get_db())
        db.query(PlayerStack).filter(PlayerStack.user_id == test_user.id).delete()
        db.commit()
        db.close()

        token = create_access_token(data={"sub": test_user.username})
        result = validate_token_and_load_user(token)

        assert result is not None
        user, stack = result
        assert stack == 1000  # Default stack

        # Verify it was created in database (use test_user.id to avoid detached instance)
        db = next(override_get_db())
        player_stack = db.query(PlayerStack).filter(PlayerStack.user_id == test_user.id).first()
        assert player_stack is not None
        assert player_stack.stack == 1000
        db.close()


class TestUpdateUserStack:
    """Test stack persistence to database."""

    def test_update_stack_success(self, test_user):
        """Test successful stack update."""
        success = update_user_stack(test_user.id, 2500)

        assert success is True

        # Verify in database
        db = next(override_get_db())
        stack = db.query(PlayerStack).filter(PlayerStack.user_id == test_user.id).first()
        assert stack.stack == 2500
        db.close()

    def test_update_stack_nonexistent_user(self):
        """Test updating stack for non-existent user."""
        success = update_user_stack(99999, 1000)

        assert success is False

    def test_update_stack_zero_chips(self, test_user):
        """Test updating stack to zero (busted player)."""
        success = update_user_stack(test_user.id, 0)

        assert success is True

        db = next(override_get_db())
        stack = db.query(PlayerStack).filter(PlayerStack.user_id == test_user.id).first()
        assert stack.stack == 0
        db.close()

    def test_update_stack_large_amount(self, test_user):
        """Test updating stack with large win."""
        success = update_user_stack(test_user.id, 50000)

        assert success is True

        db = next(override_get_db())
        stack = db.query(PlayerStack).filter(PlayerStack.user_id == test_user.id).first()
        assert stack.stack == 50000
        db.close()


class TestStackPersistence:
    """Test full stack persistence workflow."""

    def test_win_persists_stack(self, test_user):
        """Test that winning chips persists to database."""
        # Load user with token
        token = create_access_token(data={"sub": test_user.username})
        result = validate_token_and_load_user(token)
        assert result is not None
        user, initial_stack = result
        assert initial_stack == 1500

        # Simulate winning 500 chips
        new_stack = initial_stack + 500
        success = update_user_stack(user.id, new_stack)
        assert success is True

        # Reload user - should have updated stack
        result = validate_token_and_load_user(token)
        user, updated_stack = result
        assert updated_stack == 2000

    def test_loss_persists_stack(self, test_user):
        """Test that losing chips persists to database."""
        token = create_access_token(data={"sub": test_user.username})
        result = validate_token_and_load_user(token)
        user, initial_stack = result

        # Simulate losing 500 chips
        new_stack = initial_stack - 500
        success = update_user_stack(user.id, new_stack)
        assert success is True

        # Reload - should have decreased stack
        result = validate_token_and_load_user(token)
        user, updated_stack = result
        assert updated_stack == 1000

    def test_bust_out_persists(self, test_user):
        """Test that going bust persists zero stack."""
        token = create_access_token(data={"sub": test_user.username})
        result = validate_token_and_load_user(token)
        user, _ = result

        # Bust out
        success = update_user_stack(user.id, 0)
        assert success is True

        # Reload - should have zero
        result = validate_token_and_load_user(token)
        user, stack = result
        assert stack == 0
