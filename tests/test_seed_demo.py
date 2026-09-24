from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from seed_demo import seed  # noqa: E402


def test_seed_creates_expected_schema_and_rows(tmp_path):
    db_path = tmp_path / "demo.db"
    count = seed(db_path=db_path, days=10, seed_value=1)

    assert db_path.exists()
    assert count > 0

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        assert rows == count
        columns = [row[1] for row in conn.execute("PRAGMA table_info(orders)")]
        assert columns == [
            "order_id",
            "customer_name",
            "region",
            "order_date",
            "product",
            "units",
            "revenue",
        ]
    finally:
        conn.close()


def test_seed_is_deterministic_for_a_given_seed(tmp_path):
    db_path1 = tmp_path / "a.db"
    db_path2 = tmp_path / "b.db"
    count1 = seed(db_path=db_path1, days=5, seed_value=7)
    count2 = seed(db_path=db_path2, days=5, seed_value=7)
    assert count1 == count2
