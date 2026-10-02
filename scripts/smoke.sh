#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then echo "ERROR: copy .env.example to .env first" >&2; exit 1; fi
set -a; source .env; set +a
PSQL=(docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB")
echo "Checking PostgreSQL connectivity..."
"${PSQL[@]}" -c 'select 1 as postgres_reachable;'

relations=(raw.raw_customers staging.stg_orders curated.fct_order_items serving.daily_sales_summary)
for relation in "${relations[@]}"; do
  count=$("${PSQL[@]}" -Atc "select count(*) from ${relation};")
  echo "${relation}: ${count} rows"
  [[ "$count" =~ ^[0-9]+$ && "$count" -gt 0 ]] || { echo "ERROR: ${relation} is empty" >&2; exit 1; }
done

echo "Serving output:"
"${PSQL[@]}" -c 'select * from serving.daily_sales_summary order by order_date;'
expected=$("${PSQL[@]}" -Atc "select count(*) from serving.daily_sales_summary where order_date = '${PIPELINE_LOGICAL_DATE}';")
[[ "$expected" -gt 0 ]] || { echo "ERROR: expected output for ${PIPELINE_LOGICAL_DATE} missing" >&2; exit 1; }

state=$(docker compose exec -T airflow-scheduler airflow dags list-runs -d retail_daily_pipeline --no-backfill -o plain 2>/dev/null | awk 'NR>1 {print $3; exit}')
if [[ -n "$state" ]]; then
  echo "Latest Airflow run state: $state"
  [[ "$state" == "success" ]] || { echo "ERROR: latest Airflow run did not succeed" >&2; exit 1; }
fi
echo "Smoke test passed."

