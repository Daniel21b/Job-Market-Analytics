.PHONY: install lint test test-unit test-spark test-integration compose-up compose-down api worker

install:
	python -m pip install -e '.[dev,spark,legacy]'

lint:
	ruff check src tests benchmarks

test: test-unit test-spark

test-unit:
	pytest -m 'not integration and not spark'

test-spark:
	pytest -m spark

test-integration:
	pytest -m integration

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down

api:
	uvicorn skill_analytics.main:app --reload --port 8000

worker:
	skill-analytics-worker
