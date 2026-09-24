from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def sqlite_db(tmp_path: Path) -> Path:
    """Create a tiny SQLite orders database for tests."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            region TEXT NOT NULL,
            order_date TEXT NOT NULL,
            product TEXT NOT NULL,
            units INTEGER NOT NULL,
            revenue REAL NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT INTO orders (customer_name, region, order_date, product, units, revenue) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("Acme Corp", "North", "2026-01-05", "Widget", 10, 100.0),
            ("Globex LLC", "South", "2026-01-06", "Gadget", 3, 90.0),
            ("Initech", "North", "2026-01-06", "Widget", 5, 50.0),
        ],
    )
    conn.commit()
    conn.close()
    return db_path
