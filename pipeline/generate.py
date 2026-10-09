"""Deterministically generate source-like retail CSV files."""

import argparse
import csv
import logging
import random
from datetime import date
from pathlib import Path

LOGGER = logging.getLogger(__name__)
FIRST_NAMES = ["Avery", "Jordan", "Morgan", "Riley", "Casey", "Taylor"]
LAST_NAMES = ["Nguyen", "Patel", "Garcia", "Smith", "Kim", "Brown"]
CATEGORIES = ["home", "electronics", "apparel", "outdoors", "beauty"]


def _write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate(logical_date: str, output_root: str = "data/generated") -> dict[str, int]:
    parsed = date.fromisoformat(logical_date)
    rng = random.Random(int(parsed.strftime("%Y%m%d")))
    prefix = parsed.strftime("%Y%m%d")
    target = Path(output_root) / logical_date
    target.mkdir(parents=True, exist_ok=True)
    LOGGER.info("stage=generate start logical_date=%s output=%s", logical_date, target)
    customers = [
        {
            "customer_id": f"C{prefix}{i:04d}",
            "first_name": rng.choice(FIRST_NAMES),
            "last_name": rng.choice(LAST_NAMES),
            "email": f"customer{i}.{prefix}@example.test",
            "created_at": logical_date,
            "logical_date": logical_date,
        }
        for i in range(1, 251)
    ]
    products = [
        {
            "product_id": f"P{prefix}{i:04d}",
            "product_name": f"{rng.choice(CATEGORIES).title()} Item {i}",
            "category": rng.choice(CATEGORIES),
            "unit_price": f"{rng.uniform(5, 250):.2f}",
            "logical_date": logical_date,
        }
        for i in range(1, 121)
    ]
    orders, items = [], []
    for i in range(1, 601):
        order_id = f"O{prefix}{i:05d}"
        orders.append(
            {
                "order_id": order_id,
                "customer_id": rng.choice(customers)["customer_id"],
                "order_date": logical_date,
                "status": rng.choice(["paid", "shipped", "delivered"]),
                "logical_date": logical_date,
            }
        )
        for line in range(1, rng.randint(2, 5) + 1):
            product = rng.choice(products)
            items.append(
                {
                    "order_item_id": f"{order_id}-{line}",
                    "order_id": order_id,
                    "product_id": product["product_id"],
                    "quantity": rng.randint(1, 4),
                    "unit_price": product["unit_price"],
                    "logical_date": logical_date,
                }
            )
    datasets = {"customers": customers, "products": products, "orders": orders, "order_items": items}
    for name, rows in datasets.items():
        _write(target / f"{name}.csv", list(rows[0]), rows)
        LOGGER.info("dataset=%s rows_written=%d", name, len(rows))
    LOGGER.info(
        "stage=generate complete logical_date=%s rows_written=%d",
        logical_date,
        sum(map(len, datasets.values())),
    )
    return {name: len(rows) for name, rows in datasets.items()}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--logical-date", required=True)
    parser.add_argument("--output-root", default="data/generated")
    args = parser.parse_args()
    generate(args.logical_date, args.output_root)
