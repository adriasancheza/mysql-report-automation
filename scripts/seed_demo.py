#!/usr/bin/env python
"""Create a small SQLite demo database with fictional sales data.

Run from the project root:

    python scripts/seed_demo.py

This creates ``demo.db`` (gitignored) with an ``orders`` table covering the
last three months, so the example reports can be run immediately without a
real MySQL server.
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "demo.db"

REGIONS = ["North", "South", "East", "West"]
PRODUCTS = ["Widget", "Gadget", "Gizmo", "Doohickey"]
CUSTOMERS = [
    "Acme Corp",
    "Globex LLC",
    "Initech",
    "Umbrella Inc",
    "Soylent Co",
    "Stark Industries",
    "Wayne Enterprises",
    "Hooli",
]

PRICE_RANGE = {
    "Widget": (8.0, 15.0),
    "Gadget": (20.0, 45.0),
    "Gizmo": (12.0, 30.0),
    "Doohickey": (5.0, 12.0),
}


def seed(db_path: Path = DB_PATH, days: int = 90, seed_value: int = 42) -> int:
    """(Re)create the demo database and return the number of orders inserted."""
    rng = random.Random(seed_value)

    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
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

        today = date.today()
        rows = []
        for day_offset in range(days):
            order_date = today - timedelta(days=day_offset)
            orders_today = rng.randint(1, 6)
            for _ in range(orders_today):
                product = rng.choice(PRODUCTS)
                low, high = PRICE_RANGE[product]
                units = rng.randint(1, 20)
                unit_price = round(rng.uniform(low, high), 2)
                revenue = round(units * unit_price, 2)
                rows.append(
                    (
                        rng.choice(CUSTOMERS),
                        rng.choice(REGIONS),
                        order_date.isoformat(),
                        product,
                        units,
                        revenue,
                    )
                )

        conn.executemany(
            """
            INSERT INTO orders (customer_name, region, order_date, product, units, revenue)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        return len(rows)
    finally:
        conn.close()


def main() -> None:
    count = seed()
    print(f"Seeded {DB_PATH} with {count} demo orders.")
    print("Try it now:")
    print("  cp .env.example .env   # or copy on Windows")
    print("  report run monthly_sales --config reports.example.yml --dry-run")


if __name__ == "__main__":
    main()
