PYTHON=python

install:
	$(PYTHON) -m pip install -r requirements.txt

infra-up:
	docker-compose up -d

migrate:
	alembic upgrade head

run:
	uvicorn app.main:app --reload

test:
	$(PYTHON) -m pytest

lint:
	ruff check .
