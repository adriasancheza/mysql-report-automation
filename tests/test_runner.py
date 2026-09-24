from __future__ import annotations

from datetime import date
from pathlib import Path

from mysql_report_automation.config import AppConfig, OutputConfig, ReportConfig, SheetConfig
from mysql_report_automation.db import get_engine
from mysql_report_automation.runner import run_report


def _config(tmp_path: Path) -> AppConfig:
    report = ReportConfig(
        name="north_orders",
        description="North region orders",
        query=(
            "SELECT region, order_date, units, revenue FROM orders "
            "WHERE region = :region ORDER BY order_date"
        ),
        parameters={"region": "North"},
        sheet=SheetConfig(title="North"),
        output=OutputConfig(formats=["xlsx", "csv"], directory="output"),
        recipients=["team@example.com"],
    )
    return AppConfig(reports=[report], base_dir=tmp_path, output=OutputConfig())


def test_run_report_writes_files_and_dry_run_skips_email(sqlite_db, tmp_path):
    engine = get_engine(f"sqlite:///{sqlite_db}")
    cfg = _config(tmp_path)

    result = run_report(cfg, engine, "north_orders", dry_run=True, today=date(2026, 1, 10))

    assert result.row_count == 2
    assert result.emailed is False
    assert len(result.output_files) == 2
    for path in result.output_files:
        assert path.exists()
