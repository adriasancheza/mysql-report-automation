from __future__ import annotations

from pathlib import Path

import pytest

from mysql_report_automation.config import ConfigError, load_config, validate_config

EXAMPLE_CONFIG = Path(__file__).resolve().parent.parent / "reports.example.yml"


def test_load_example_config():
    cfg = load_config(EXAMPLE_CONFIG)
    assert cfg.database_url_env == "DATABASE_URL"
    names = [r.name for r in cfg.reports]
    assert "monthly_sales" in names
    assert "daily_orders" in names


def test_get_report_found_and_missing():
    cfg = load_config(EXAMPLE_CONFIG)
    report = cfg.get_report("monthly_sales")
    assert report.description
    with pytest.raises(ConfigError):
        cfg.get_report("does_not_exist")


def test_validate_example_config_has_no_errors():
    cfg = load_config(EXAMPLE_CONFIG)
    assert validate_config(cfg) == []


def test_missing_file_raises():
    with pytest.raises(ConfigError):
        load_config("does/not/exist.yml")


def test_report_requires_query_or_query_file(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text(
        "reports:\n  - name: broken\n    recipients: []\n",
        encoding="utf-8",
    )
    cfg = load_config(bad)
    errors = validate_config(cfg)
    assert any("query" in e for e in errors)


def test_duplicate_report_names_raise(tmp_path):
    bad = tmp_path / "dup.yml"
    bad.write_text(
        "reports:\n"
        "  - name: same\n    query: 'SELECT 1'\n"
        "  - name: same\n    query: 'SELECT 2'\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_config(bad)


def test_empty_reports_list_raises(tmp_path):
    bad = tmp_path / "empty.yml"
    bad.write_text("reports: []\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(bad)


def test_unsupported_output_format_flagged(tmp_path):
    bad = tmp_path / "fmt.yml"
    bad.write_text(
        "reports:\n"
        "  - name: r\n    query: 'SELECT 1'\n    output:\n      formats: [xlsx, pdf]\n",
        encoding="utf-8",
    )
    cfg = load_config(bad)
    errors = validate_config(cfg)
    assert any("pdf" in e for e in errors)
