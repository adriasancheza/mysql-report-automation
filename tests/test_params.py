from __future__ import annotations

from datetime import date

from mysql_report_automation.params import resolve_param, resolve_parameters


def test_today_and_yesterday():
    today = date(2026, 3, 15)
    assert resolve_param("today", today=today) == today
    assert resolve_param("yesterday", today=today) == date(2026, 3, 14)
    assert resolve_param("tomorrow", today=today) == date(2026, 3, 16)


def test_last_month_bounds_handles_year_rollover():
    today = date(2026, 1, 10)
    assert resolve_param("last_month_start", today=today) == date(2025, 12, 1)
    assert resolve_param("last_month_end", today=today) == date(2025, 12, 31)


def test_this_month_bounds():
    today = date(2026, 2, 15)
    assert resolve_param("this_month_start", today=today) == date(2026, 2, 1)
    assert resolve_param("this_month_end", today=today) == date(2026, 2, 28)


def test_unrecognised_string_passes_through():
    assert resolve_param("not_a_keyword", today=date(2026, 1, 1)) == "not_a_keyword"
    assert resolve_param(42, today=date(2026, 1, 1)) == 42


def test_resolve_parameters_dict():
    today = date(2026, 6, 1)
    resolved = resolve_parameters(
        {"start_date": "last_month_start", "end_date": "last_month_end", "region": "North"},
        today=today,
    )
    assert resolved == {
        "start_date": date(2026, 5, 1),
        "end_date": date(2026, 5, 31),
        "region": "North",
    }


def test_resolve_parameters_empty():
    assert resolve_parameters(None) == {}
    assert resolve_parameters({}) == {}
