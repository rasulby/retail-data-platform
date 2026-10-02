.PHONY: init up down logs trigger smoke test lint compile config dbt-parse

DATE ?= 2026-01-01

init:
	docker compose up airflow-init

up: init
	docker compose up -d airflow-webserver airflow-scheduler

down:
	docker compose down

logs:
	docker compose logs -f airflow-scheduler airflow-webserver

trigger:
	docker compose exec airflow-scheduler airflow dags trigger retail_daily_pipeline --conf '{"logical_date":"$(DATE)"}'

smoke:
	bash scripts/smoke.sh

test:
	pytest -q

lint:
	ruff check pipeline tests airflow/dags

compile:
	python -m compileall -q pipeline airflow/dags tests

config:
	docker compose config --quiet

dbt-parse:
	docker compose run --rm airflow-scheduler bash -c 'cd /opt/airflow/project/dbt && dbt parse --profiles-dir .'

