.PHONY: prepare init up down logs trigger smoke test lint compile config dbt-parse dbt-staging

DATE ?= 2026-01-01

prepare:
	mkdir -p data/generated logs
	chmod 0777 data data/generated logs

init: prepare
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
	docker compose run --rm airflow-scheduler dbt parse --project-dir /opt/airflow/project/dbt --profiles-dir /opt/airflow/project/dbt

dbt-staging:
	docker compose run --rm airflow-scheduler dbt run --profiles-dir /opt/airflow/project/dbt --project-dir /opt/airflow/project/dbt --fail-fast --select tag:staging
