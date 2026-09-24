from __future__ import annotations

import pytest

from mysql_report_automation.db import DatabaseError, get_database_url, get_engine, run_query


def test_get_database_url_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(DatabaseError):
        get_database_url()


def test_get_database_url_present(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    assert get_database_url() == "sqlite:///:memory:"


def test_run_query_against_sqlite(sqlite_db):
    engine = get_engine(f"sqlite:///{sqlite_db}")
    result = run_query(
        engine,
        "SELECT region, SUM(units) AS units FROM orders WHERE region = :region GROUP BY region",
        {"region": "North"},
    )
    assert result.columns == ["region", "units"]
    assert result.row_count == 1
    assert result.rows[0] == ("North", 15)


def test_run_query_invalid_sql_raises(sqlite_db):
    engine = get_engine(f"sqlite:///{sqlite_db}")
    with pytest.raises(DatabaseError):
        run_query(engine, "SELECT * FROM not_a_table")
