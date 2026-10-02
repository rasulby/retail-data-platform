# Phase 1 Evidence

This file never substitutes invented results for execution evidence. Static checks recorded below were run during implementation. Docker was unavailable in that environment, so runtime sections are explicitly awaiting owner execution.

## Successful Pipeline Run

[SCREENSHOT REQUIRED: Successful `retail_daily_pipeline` Airflow graph/grid run showing all six green tasks.]

Owner command: `make trigger DATE=2026-01-01` after `make up`.

## Deliberate Failed Run

[SCREENSHOT REQUIRED: Failed Airflow run showing `ingest_raw` failed and every downstream task not executed.]

Follow the README deliberate-failure procedure and capture the Grid view after retries finish.

## Smoke Test

[OUTPUT REQUIRED: Run `make smoke` after a successful pipeline and paste its complete output here.]

## Layer Row Counts

[OUTPUT REQUIRED: Capture the four row counts printed by `make smoke`.]

## Idempotency Test

[OUTPUT REQUIRED: Run the same logical date twice and record the before/after raw counts. They must match.]

## Multiple Logical Dates Test

[OUTPUT REQUIRED: Run 2026-01-01 and 2026-01-02 and capture the grouped `logical_date` query from the README.]

## Infrastructure Restart / Persistence Test

[OUTPUT REQUIRED: Record counts before `make down` and after `make up`; the named-volume-backed counts must match.]

## Static Validation Performed During Implementation

- `python -m compileall -q pipeline airflow/dags tests` — passed.
- `ruff check pipeline tests airflow/dags` — passed.
- `pytest -q` — passed (2 tests).
- `docker compose config --quiet` — not executable because Docker/Compose was not installed in the implementation environment.
- `dbt parse --project-dir dbt --profiles-dir dbt` — not executable because dbt was not installed on the host; it is installed in the project image.

Runtime evidence is intentionally not claimed until Docker execution occurs.
