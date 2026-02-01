.PHONY: test test-backend test-frontend install-backend install-frontend install

# Run all tests
test:
	@./scripts/test.sh

# Run backend tests only
test-backend:
	cd server && source .venv/bin/activate && python -m pytest

# Run frontend tests only
test-frontend:
	cd poker-client && npm test -- --run

# Run tests with coverage
test-coverage:
	cd server && source .venv/bin/activate && python -m pytest --cov-report=html
	cd poker-client && npm run test:coverage

# Install all dependencies
install: install-backend install-frontend

# Install backend dependencies
install-backend:
	cd server && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt

# Install frontend dependencies
install-frontend:
	cd poker-client && npm install

# Start development servers
dev:
	@echo "Start backend: cd server && source .venv/bin/activate && uvicorn app.main:app --reload"
	@echo "Start frontend: cd poker-client && npm run dev"
