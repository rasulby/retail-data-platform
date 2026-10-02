import csv

from pipeline.generate import generate


def test_generator_is_deterministic_and_large(tmp_path):
    first = generate("2026-01-01", str(tmp_path))
    item_path = tmp_path / "2026-01-01" / "order_items.csv"
    original = item_path.read_text(encoding="utf-8")
    second = generate("2026-01-01", str(tmp_path))
    assert first == second
    assert first["order_items"] > 1_000
    assert item_path.read_text(encoding="utf-8") == original
    assert len(list(csv.DictReader(item_path.open(encoding="utf-8")))) == first["order_items"]


def test_dates_have_distinct_keys(tmp_path):
    generate("2026-01-01", str(tmp_path))
    generate("2026-01-02", str(tmp_path))
    first = next(csv.DictReader((tmp_path / "2026-01-01/customers.csv").open(encoding="utf-8")))
    second = next(csv.DictReader((tmp_path / "2026-01-02/customers.csv").open(encoding="utf-8")))
    assert first["customer_id"] != second["customer_id"]
    assert first["logical_date"] != second["logical_date"]
