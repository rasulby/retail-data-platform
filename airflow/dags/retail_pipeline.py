"""Airflow orchestration for the complete retail batch pipeline."""

from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator

from airflow import DAG

DATE = "{{ dag_run.conf.get('logical_date', ds) if dag_run else ds }}"
DBT = "cd /opt/airflow/project/dbt && dbt --profiles-dir ."

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
        bash_command=f"cd /opt/airflow/project && python -m pipeline.generate --logical-date '{DATE}'",
    )
    ingest_raw = BashOperator(
        task_id="ingest_raw",
        bash_command=f"cd /opt/airflow/project && python -m pipeline.ingest --logical-date '{DATE}'",
        retries=2,
        retry_delay=timedelta(minutes=1),
    )
    dbt_staging = BashOperator(task_id="dbt_staging", bash_command=f"{DBT} run --select path:models/staging")
    dbt_curated = BashOperator(task_id="dbt_curated", bash_command=f"{DBT} run --select path:models/curated")
    data_quality = BashOperator(
        task_id="data_quality",
        bash_command=f"{DBT} test --select path:models/staging path:models/curated",
    )
    publish_serving = BashOperator(
        task_id="publish_serving",
        bash_command=f"{DBT} run --select path:models/serving && {DBT} test --select path:models/serving",
    )

    generate_data >> ingest_raw >> dbt_staging >> dbt_curated >> data_quality >> publish_serving
