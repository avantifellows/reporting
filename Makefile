.PHONY: setup run test lint clean docker-up docker-down

# Setup project
setup:
	pip install -r app/requirements.txt
	pip install pre-commit
	pre-commit install

# Run the application
run:
	cd app && uvicorn main:app --port 5050 --reload

# Run tests
test:
	cd app && pytest

# Lint code
lint:
	cd app && flake8 .
	cd app && black . --check

# Format code
format:
	cd app && black .

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

# Start Docker containers
docker-up:
	docker volume create --name=dynamodb_data
	docker-compose up --build -d

# Stop Docker containers
docker-down:
	docker-compose down

# A full setup for first-time local development
dev-setup: setup docker-up
	@echo "Now connect to the app container and run 'python generate_table' to create the database tables"

# Help command
help:
	@echo "Available commands:"
	@echo "  setup      - Install dependencies and set up pre-commit hooks"
	@echo "  run        - Run the application locally"
	@echo "  test       - Run tests"
	@echo "  lint       - Check code style"
	@echo "  format     - Format code with Black"
	@echo "  clean      - Remove temporary files"
	@echo "  docker-up  - Start Docker containers"
	@echo "  docker-down- Stop Docker containers"
	@echo "  dev-setup  - Full setup for first-time development"
