.PHONY: install seed engine services dashboard matrix test

install:
	pip install -r requirements.txt

seed:
	python -m mcp_servers.seed_kb

engine:
	python -m engine --strategy fifo --duration 20 --rate 2 --json-out fifo_summary.json

services:
	uvicorn services.app:app --port 8000

dashboard:
	uvicorn dashboard.backend.server:app --port 8080
	@echo "open http://localhost:8080/"

matrix:
	python -m agents.run_scenario --framework all --scenario asi01 --matrix matrix.json

test:
	CKA_TIME_SCALE=0.02 pytest -q
