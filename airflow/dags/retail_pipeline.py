"""Airflow orchestration for the complete retail batch pipeline."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

DATE = "{{ dag_run.conf.get('logical_date', ds) if dag_run else ds }}"
PROJECT = "cd /opt/airflow/project &&"
DBT_PATHS = "--profiles-dir /opt/airflow/project/dbt --project-dir /opt/airflow/project/dbt"

with DAG(
    dag_id="retail_daily_pipeline",
    description="Generate, ingest, transform, test, and publish retail data",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={"owner": "data-engineering", "retries": 0},
    tags=["retail", "phase-1"],
) as dag:
    generate_data = BashOperator(
        task_id="generate_data",
        bash_command=f"{PROJECT} python -m pipeline.generate --logical-date '{DATE}'",
    )
    ingest_raw = BashOperator(
        task_id="ingest_raw",
        bash_command=f"{PROJECT} python -m pipeline.ingest --logical-date '{DATE}'",
        retries=2,
        retry_delay=timedelta(minutes=1),
    )
    dbt_staging = BashOperator(
        task_id="dbt_staging",
        bash_command=f"dbt run {DBT_PATHS} --fail-fast --select tag:staging",
    )
    dbt_curated = BashOperator(
        task_id="dbt_curated",
        bash_command=f"dbt run {DBT_PATHS} --fail-fast --select tag:curated",
    )
    data_quality = BashOperator(
        task_id="data_quality",
        bash_command=f"dbt test {DBT_PATHS} --fail-fast --select tag:staging tag:curated",
    )
    publish_serving = BashOperator(
        task_id="publish_serving",
        bash_command=(
            f"dbt run {DBT_PATHS} --fail-fast --select tag:serving && "
            f"dbt test {DBT_PATHS} --fail-fast --select tag:serving"
        ),
    )

    generate_data >> ingest_raw >> dbt_staging >> dbt_curated >> data_quality >> publish_serving
