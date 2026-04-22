.PHONY: install run-api run-web run-subset test

install:
	python -m pip install -r services/enricher/requirements.txt
	cd apps/web && npm install

run-api:
	uvicorn services.enricher.main:app --reload --port 8000

run-web:
	cd apps/web && npm run dev

run-subset:
	python services/enricher/run_pipeline.py

test:
	cd services/enricher && python -m pytest -q
