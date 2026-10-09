"""Load generated CSV partitions into PostgreSQL raw tables."""

import argparse
import csv
import logging
import os
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

from pipeline.config import database_config

LOGGER = logging.getLogger(__name__)
TABLES = {
    "customers": (["customer_id", "first_name", "last_name", "email", "created_at", "logical_date"], "raw_customers"),
    "products": (["product_id", "product_name", "category", "unit_price", "logical_date"], "raw_products"),
    "orders": (["order_id", "customer_id", "order_date", "status", "logical_date"], "raw_orders"),
    "order_items": (
        ["order_item_id", "order_id", "product_id", "quantity", "unit_price", "logical_date"],
        "raw_order_items",
    ),
}

DDL = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.raw_customers (
  customer_id text PRIMARY KEY, first_name text, last_name text, email text,
  created_at date, logical_date date NOT NULL
);
CREATE TABLE IF NOT EXISTS raw.raw_products (
  product_id text PRIMARY KEY, product_name text, category text,
  unit_price numeric(12,2), logical_date date NOT NULL
);
CREATE TABLE IF NOT EXISTS raw.raw_orders (
  order_id text PRIMARY KEY, customer_id text, order_date date,
  status text, logical_date date NOT NULL
);
CREATE TABLE IF NOT EXISTS raw.raw_order_items (
  order_item_id text PRIMARY KEY, order_id text, product_id text, quantity integer,
  unit_price numeric(12,2), logical_date date NOT NULL
);
"""


def ingest(logical_date: str, input_root: str = "data/generated") -> dict[str, int]:
    if os.getenv("FORCE_INGEST_FAILURE", "false").lower() == "true":
        raise RuntimeError("Deliberate ingestion failure: FORCE_INGEST_FAILURE=true")
    source = Path(input_root) / logical_date
    LOGGER.info("stage=ingest start logical_date=%s input=%s output=PostgreSQL/raw", logical_date, source)
    counts = {}
    with psycopg2.connect(**database_config()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(DDL)
            for name, (columns, table) in TABLES.items():
                with (source / f"{name}.csv").open(encoding="utf-8") as handle:
                    rows = [[row[column] for column in columns] for row in csv.DictReader(handle)]
                cursor.execute(f"DELETE FROM raw.{table} WHERE logical_date = %s", (logical_date,))
                execute_values(cursor, f"INSERT INTO raw.{table} ({','.join(columns)}) VALUES %s", rows)
                counts[name] = len(rows)
                LOGGER.info("table=raw.%s rows_read=%d rows_written=%d", table, len(rows), len(rows))
    LOGGER.info("stage=ingest complete logical_date=%s rows_written=%d", logical_date, sum(counts.values()))
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--logical-date", required=True)
    parser.add_argument("--input-root", default="data/generated")
    args = parser.parse_args()
    ingest(args.logical_date, args.input_root)
