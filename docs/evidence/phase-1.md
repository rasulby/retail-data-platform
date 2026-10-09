# Phase 1 Evidence

## Evidence policy and status

This document distinguishes **observed evidence** from **evidence still requiring a
Docker-capable host**. Nothing below is a fabricated pipeline result.

Evidence collection date: `2026-10-05T15:11:55Z`<br>
Code revision evaluated by the static checks: `638337c7bfa11478895eb6baffb1c17b48e8e098`

| Evidence | Status | Location |
|---|---|---|
| Python compilation | **PASS — observed** | Static Validation |
| Ruff lint | **PASS — observed** | Static Validation |
| Unit/configuration tests | **PASS — observed** | Static Validation |
| Synthetic source volume | **PASS — observed** | Synthetic Source Evidence |
| Deterministic source rerun | **PASS — observed** | Synthetic Source Evidence |
| Successful Airflow pipeline | **NOT VERIFIED — Docker unavailable** | Successful Pipeline Run |
| Deliberate failed Airflow run | **NOT VERIFIED — Docker unavailable** | Deliberate Failed Run |
| Integration smoke test | **NOT VERIFIED — Docker unavailable** | Smoke Test |
| Database idempotency/multiple dates/persistence | **NOT VERIFIED — Docker unavailable** | Sections below |

The implementation environment returned `docker: command not found` for both
`docker --version` and `docker compose version`. Consequently, this file does not
claim that PostgreSQL, Airflow, or dbt executed successfully.

## How to verify and collect the remaining evidence

Run this section from the repository root on a machine with Docker Engine and
Docker Compose. Commands that trigger a DAG are asynchronous: after each trigger,
wait in the Airflow UI at <http://localhost:8080> until the run reaches a terminal
state before collecting its database results. The local credentials from
`.env.example` are `admin` / `admin`.

### 1. Prepare and validate the project

```bash
cp .env.example .env
make config
make test
make lint
make compile
make up
docker compose ps
```

Acceptance: the validation commands exit with status `0`; `postgres`,
`airflow-scheduler`, and `airflow-webserver` are running (and healthy where a
health check is defined).

### 2. Run the successful pipeline

```bash
make trigger DATE=2026-01-01
docker compose exec airflow-scheduler \
  airflow dags list-runs -d retail_daily_pipeline -o table
```

Repeat the `list-runs` command until the newest run is `success`. Open the newest
run in the Airflow Grid view and capture one screenshot showing all six green
tasks. Paste the command output and screenshot into **Successful Pipeline Run**.
Do not mark it verified while the state is `queued` or `running`.

### 3. Prove all data layers and the serving result

```bash
make smoke

docker compose exec -T postgres psql -U retail -d retail -c "
select 'raw.raw_customers' as relation, count(*) from raw.raw_customers
union all select 'raw.raw_products', count(*) from raw.raw_products
union all select 'raw.raw_orders', count(*) from raw.raw_orders
union all select 'raw.raw_order_items', count(*) from raw.raw_order_items
union all select 'staging.stg_orders', count(*) from staging.stg_orders
union all select 'curated.fct_orders', count(*) from curated.fct_orders
union all select 'curated.fct_order_items', count(*) from curated.fct_order_items
union all select 'serving.daily_sales_summary', count(*) from serving.daily_sales_summary;
"

docker compose exec -T postgres psql -U retail -d retail -c \
  "select * from serving.daily_sales_summary where order_date='2026-01-01';"
```

Acceptance: `make smoke` ends with `Smoke test passed.`, every layer count is
greater than zero, and the final query returns the `2026-01-01` summary. Paste
these outputs into **Smoke Test** and **Layer Row Counts**.

### 4. Prove same-date idempotency

Run the count query below, rerun the same date, wait for Airflow success, and run
the identical query again:

```bash
docker compose exec -T postgres psql -U retail -d retail -c "
select 'customers' as dataset, count(*) from raw.raw_customers where logical_date='2026-01-01'
union all select 'products', count(*) from raw.raw_products where logical_date='2026-01-01'
union all select 'orders', count(*) from raw.raw_orders where logical_date='2026-01-01'
union all select 'order_items', count(*) from raw.raw_order_items where logical_date='2026-01-01';
"
make trigger DATE=2026-01-01
docker compose exec airflow-scheduler \
  airflow dags list-runs -d retail_daily_pipeline -o table
# Wait for the new run to succeed, then execute the same psql query again.
```

Acceptance: the two snapshots are identical (`250`, `120`, `600`, and the same
order-item count), and both Airflow runs succeeded. Paste both snapshots into
**Idempotency Test**.

### 5. Prove that two logical dates coexist

```bash
make trigger DATE=2026-01-02
docker compose exec airflow-scheduler \
  airflow dags list-runs -d retail_daily_pipeline -o table
# Wait for success before querying PostgreSQL.
docker compose exec -T postgres psql -U retail -d retail -c "
select logical_date, count(*) as orders
from raw.raw_orders
where logical_date in ('2026-01-01', '2026-01-02')
group by logical_date
order by logical_date;
"
```

Acceptance: the query returns both dates with `600` orders each. Paste it into
**Multiple Logical Dates Test**.

### 6. Prove restart persistence

```bash
docker compose exec -T postgres psql -U retail -d retail -Atc \
  "select count(*) from raw.raw_orders;"
make down
make up
docker compose exec -T postgres psql -U retail -d retail -Atc \
  "select count(*) from raw.raw_orders;"
```

Acceptance: the before and after counts are equal. Never add `-v` to `make down`
or `docker compose down`, because `-v` deletes the PostgreSQL named volume.

### 7. Prove failure propagation

Change only `FORCE_INGEST_FAILURE` in `.env`, recreate the Airflow services so
they receive the new environment value, and trigger an unused date:

```bash
sed -i.bak 's/^FORCE_INGEST_FAILURE=.*/FORCE_INGEST_FAILURE=true/' .env
docker compose up -d --force-recreate airflow-webserver airflow-scheduler
make trigger DATE=2026-01-03
docker compose exec airflow-scheduler \
  airflow dags list-runs -d retail_daily_pipeline -o table
```

Wait until the run is `failed`, then capture the Grid view. `ingest_raw` must be
red after its retries; `dbt_staging`, `dbt_curated`, `data_quality`, and
`publish_serving` must not run. Paste the output and screenshot into
**Deliberate Failed Run**.

Restore normal operation when the evidence has been collected:

```bash
mv .env.bak .env
docker compose up -d --force-recreate airflow-webserver airflow-scheduler
```

Only replace a `NOT VERIFIED` status or an `[OUTPUT/SCREENSHOT REQUIRED]`
placeholder after its acceptance criteria have actually passed. Record the date,
Git commit (`git rev-parse HEAD`), commands, and unedited output so another
reviewer can reproduce the evidence.

## Synthetic Source Evidence

The real generator was executed outside Docker with:

```bash
rm -rf /tmp/retail-evidence
python -m pipeline.generate \
  --logical-date 2026-01-01 \
  --output-root /tmp/retail-evidence
```

Observed output:

```text
INFO stage=generate start logical_date=2026-01-01 output=/tmp/retail-evidence/2026-01-01
INFO dataset=customers rows_written=250
INFO dataset=products rows_written=120
INFO dataset=orders rows_written=600
INFO dataset=order_items rows_written=2098
INFO stage=generate complete logical_date=2026-01-01 rows_written=3068
```

Counts independently read from the generated CSV files (header excluded):

```text
customers=250
products=120
orders=600
order_items=2098
```

This proves that the largest source table contains more than 1,000 rows.

The same logical date was generated a second time. SHA-256 values were identical
before and after the rerun:

```text
b004e7313b6be1b9acdee633e3d3e7a732885d758e3e913b46da091df7fb1c42  customers.csv
26d45c5639e08612bcbf0d6b2f7cc754a556a99469b3e3faa3ea6aea6c2749cf  order_items.csv
9d675f60afd86dfa6ab1e224249bbd8781e45a775c25630bcdec8b216a231f3d  orders.csv
9d4a80ec6113ded06ebbb6815e6df018c19e397917dd6ca38c1a1c76c628a509  products.csv
```

This is generator determinism evidence only. Database idempotency requires the
separate Docker-backed test below.

## Successful Pipeline Run

**Status: NOT VERIFIED — Docker was unavailable.**

Run:

```bash
cp .env.example .env
make up
make trigger DATE=2026-01-01
docker compose exec airflow-scheduler \
  airflow dags list-runs -d retail_daily_pipeline -o table
```

Acceptance evidence:

- DAG run state is `success`.
- `generate_data`, `ingest_raw`, `dbt_staging`, `dbt_curated`, `data_quality`,
  and `publish_serving` are all green.
- The `dbt_staging` log shows four staging models completed.

> [SCREENSHOT REQUIRED: Airflow Grid view for the successful 2026-01-01 run,
> showing all six tasks in green.]

> [OUTPUT REQUIRED: Paste the corresponding `airflow dags list-runs` row here.]

## Deliberate Failed Run

**Status: NOT VERIFIED — Docker was unavailable.**

Run the README deliberate-failure procedure with
`FORCE_INGEST_FAILURE=true`, recreate the Airflow containers, and trigger
`2026-01-03`.

Acceptance evidence:

- `ingest_raw` is failed after its configured retries.
- All downstream tasks are `upstream_failed` and do not execute.
- The overall DAG run is `failed`.

> [SCREENSHOT REQUIRED: Airflow Grid view showing failed `ingest_raw` and
> blocked downstream tasks.]

> [OUTPUT REQUIRED: Paste the failed `airflow dags list-runs` row here.]

## Smoke Test

**Status: NOT VERIFIED — Docker was unavailable.**

After the successful pipeline run, execute:

```bash
make smoke
```

The script itself passed shell syntax validation with
`bash -n scripts/smoke.sh`. Runtime acceptance requires exit code `0`, printed
counts greater than zero for every layer, a serving result for `2026-01-01`, and
latest Airflow state `success`.

> [OUTPUT REQUIRED: Paste the complete `make smoke` output, including its
> `Smoke test passed.` final line.]

## Layer Row Counts

**Status: NOT VERIFIED — PostgreSQL was unavailable.**

Collect the counts with:

```bash
docker compose exec -T postgres psql -U retail -d retail -c "
select 'raw.raw_customers' as relation, count(*) from raw.raw_customers
union all select 'raw.raw_products', count(*) from raw.raw_products
union all select 'raw.raw_orders', count(*) from raw.raw_orders
union all select 'raw.raw_order_items', count(*) from raw.raw_order_items
union all select 'staging.stg_orders', count(*) from staging.stg_orders
union all select 'curated.fct_orders', count(*) from curated.fct_orders
union all select 'curated.fct_order_items', count(*) from curated.fct_order_items
union all select 'serving.daily_sales_summary', count(*) from serving.daily_sales_summary;
"
```

> [OUTPUT REQUIRED: Paste the returned layer counts here. Every count must be
> greater than zero.]

## Idempotency Test

**Status: NOT VERIFIED — Airflow/PostgreSQL were unavailable.**

1. Trigger `2026-01-01` and wait for success.
2. Record the four raw counts for that logical date.
3. Trigger `2026-01-01` again and wait for success.
4. Record the counts again and compare them.

```bash
make trigger DATE=2026-01-01
docker compose exec -T postgres psql -U retail -d retail -c "
select 'customers' as dataset, count(*) from raw.raw_customers where logical_date='2026-01-01'
union all select 'products', count(*) from raw.raw_products where logical_date='2026-01-01'
union all select 'orders', count(*) from raw.raw_orders where logical_date='2026-01-01'
union all select 'order_items', count(*) from raw.raw_order_items where logical_date='2026-01-01';
"
```

Acceptance: first-run and second-run counts are identical, with no duplicate
business keys.

> [OUTPUT REQUIRED: Paste both count snapshots here.]

## Multiple Logical Dates Test

**Status: NOT VERIFIED — Airflow/PostgreSQL were unavailable.**

```bash
make trigger DATE=2026-01-02
docker compose exec -T postgres psql -U retail -d retail -c "
select logical_date, count(*) as orders
from raw.raw_orders
where logical_date in ('2026-01-01', '2026-01-02')
group by logical_date
order by logical_date;
"
```

Acceptance: both dates exist and each has `600` raw orders.

> [OUTPUT REQUIRED: Paste the two returned date rows here.]

## Infrastructure Restart / Persistence Test

**Status: NOT VERIFIED — Docker/PostgreSQL were unavailable.**

```bash
docker compose exec -T postgres psql -U retail -d retail -Atc \
  "select count(*) from raw.raw_orders;"
make down
make up
docker compose exec -T postgres psql -U retail -d retail -Atc \
  "select count(*) from raw.raw_orders;"
```

Acceptance: the counts before and after restart are identical. Do not use
`docker compose down -v`, because that intentionally removes the named volume.

> [OUTPUT REQUIRED: Paste the before-and-after counts here.]

## Static Validation

Commands executed on `2026-10-05` and their observed results:

```text
$ python -m compileall -q pipeline airflow/dags tests
PASS (exit 0)

$ ruff check pipeline tests airflow/dags
All checks passed!

$ pytest -q
.....                                                                    [100%]
5 passed in 0.12s

$ bash -n scripts/smoke.sh
PASS (exit 0)

$ git diff --check
PASS (exit 0)
```

The following checks remain pending rather than being presented as successful:

```text
docker compose config --quiet
dbt parse --project-dir dbt --profiles-dir dbt
make smoke
```

They require Docker or a host dbt installation, neither of which was available
in the evidence-collection environment.
