from pathlib import Path


def test_all_staging_models_are_tagged_and_selectable():
    project = Path("dbt/dbt_project.yml").read_text(encoding="utf-8")
    models = sorted(Path("dbt/models/staging").glob("*.sql"))

    assert "+tags: [staging]" in project
    assert [model.stem for model in models] == [
        "stg_customers",
        "stg_order_items",
        "stg_orders",
        "stg_products",
    ]


def test_airflow_dbt_commands_put_subcommand_before_flags():
    dag = Path("airflow/dags/retail_pipeline.py").read_text(encoding="utf-8")

    assert 'bash_command=f"dbt run {DBT_PATHS} --fail-fast --select tag:staging"' in dag
    assert 'bash_command=f"dbt run {DBT_PATHS} --fail-fast --select tag:curated"' in dag
    assert 'bash_command=f"dbt test {DBT_PATHS} --fail-fast' in dag
    assert 'f"dbt run {DBT_PATHS} --fail-fast --select tag:serving' in dag
    assert "dbt --profiles-dir" not in dag


def test_dbt_subcommand_precedes_flags_in_operational_files():
    makefile = Path("Makefile").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "airflow-scheduler dbt parse --project-dir" in makefile
    assert "run: dbt parse --project-dir" in workflow
    assert "run: dbt ls --quiet --project-dir" in workflow
    assert "`dbt run --profiles-dir ...`" in readme
    assert "`dbt test --profiles-dir ...`" in readme
