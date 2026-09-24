"""Resolve named date parameters (e.g. "last_month", "yesterday") to concrete values.

Report queries reference parameters like ``:start_date`` / ``:end_date``. Instead of
hard-coding dates in YAML, report authors use a small vocabulary of relative-date
keywords that get resolved at run time relative to "today".
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Any


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    first = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = date(year, month, last_day)
    return first, last


def _shift_month(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


# Registry of keyword -> function(today) -> value
_KEYWORDS: dict[str, Any] = {
    "today": lambda today: today,
    "yesterday": lambda today: today - timedelta(days=1),
    "tomorrow": lambda today: today + timedelta(days=1),
    "this_month_start": lambda today: _month_bounds(today.year, today.month)[0],
    "this_month_end": lambda today: _month_bounds(today.year, today.month)[1],
    "last_month_start": lambda today: _month_bounds(
        _shift_month(today, -1).year, _shift_month(today, -1).month
    )[0],
    "last_month_end": lambda today: _month_bounds(
        _shift_month(today, -1).year, _shift_month(today, -1).month
    )[1],
    "next_month_start": lambda today: _month_bounds(
        _shift_month(today, 1).year, _shift_month(today, 1).month
    )[0],
    "this_week_start": lambda today: today - timedelta(days=today.weekday()),
    "this_week_end": lambda today: today - timedelta(days=today.weekday()) + timedelta(days=6),
    "last_week_start": lambda today: today - timedelta(days=today.weekday() + 7),
    "last_week_end": lambda today: today - timedelta(days=today.weekday() + 1),
    "last_7_days_start": lambda today: today - timedelta(days=7),
    "last_30_days_start": lambda today: today - timedelta(days=30),
    "year_start": lambda today: date(today.year, 1, 1),
    "year_end": lambda today: date(today.year, 12, 31),
    "last_year_start": lambda today: date(today.year - 1, 1, 1),
    "last_year_end": lambda today: date(today.year - 1, 12, 31),
}


def available_keywords() -> list[str]:
    """Return the sorted list of supported relative-date keywords."""
    return sorted(_KEYWORDS)


def resolve_param(value: Any, today: date | None = None) -> Any:
    """Resolve a single parameter value.

    If ``value`` is a string matching a known keyword, it is replaced by the
    corresponding date. Any other value (including plain strings, numbers, or
    unrecognised strings) is passed through unchanged as a literal.
    """
    today = today or date.today()
    if isinstance(value, str) and value in _KEYWORDS:
        return _KEYWORDS[value](today)
    return value


def resolve_parameters(
    params: dict[str, Any] | None, today: date | None = None
) -> dict[str, Any]:
    """Resolve every value in a parameters mapping. Returns a new dict."""
    if not params:
        return {}
    today = today or date.today()
    return {key: resolve_param(value, today=today) for key, value in params.items()}
