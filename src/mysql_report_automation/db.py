"""Database connection and query execution helpers, built on SQLAlchemy Core."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class DatabaseError(Exception):
    """Raised for connection or query execution failures."""


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[tuple[Any, ...]]

    @property
    def row_count(self) -> int:
        return len(self.rows)


def get_database_url(env_var: str = "DATABASE_URL") -> str:
    """Read the SQLAlchemy connection URL from an environment variable."""
    url = os.environ.get(env_var)
    if not url:
        raise DatabaseError(
            f"Environment variable '{env_var}' is not set. "
            "Copy .env.example to .env and configure your database URL."
        )
    return url


def get_engine(url: str, *, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine for the given connection URL."""
    try:
        return create_engine(url, echo=echo, future=True)
    except Exception as exc:  # pragma: no cover - defensive, SQLAlchemy validates lazily
        raise DatabaseError(f"Could not create database engine: {exc}") from exc


def run_query(engine: Engine, sql: str, params: dict[str, Any] | None = None) -> QueryResult:
    """Execute a parameterised SQL query and return columns + rows."""
    params = params or {}
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql), params)
            columns = list(result.keys())
            rows = [tuple(row) for row in result.fetchall()]
    except Exception as exc:
        raise DatabaseError(f"Query execution failed: {exc}") from exc
    return QueryResult(columns=columns, rows=rows)
