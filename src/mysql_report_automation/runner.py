"""Orchestrates a single report run: query -> workbook/CSV -> email."""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.engine import Engine

from mysql_report_automation.config import AppConfig, ReportConfig
from mysql_report_automation.db import run_query
from mysql_report_automation.email_sender import send_report_email
from mysql_report_automation.excel import build_workbook, save_csv, save_xlsx
from mysql_report_automation.params import resolve_parameters

logger = logging.getLogger(__name__)


@dataclass
class ReportRunResult:
    report_name: str
    row_count: int
    output_files: list[Path]
    emailed: bool


def run_report(
    config: AppConfig,
    engine: Engine,
    report_name: str,
    *,
    dry_run: bool = False,
    today: dt.date | None = None,
) -> ReportRunResult:
    """Run a single report: execute its query, write output file(s), send email."""
    report: ReportConfig = config.get_report(report_name)
    logger.info("Running report '%s'", report.name)

    sql = report.resolve_query(config.base_dir)
    params = resolve_parameters(report.parameters, today=today)
    logger.debug("Resolved parameters for '%s': %s", report.name, params)

    result = run_query(engine, sql, params)
    logger.info("Report '%s' returned %d row(s)", report.name, result.row_count)

    output_dir = config.base_dir / report.output.directory
    output_files: list[Path] = []

    if "xlsx" in report.output.formats:
        workbook = build_workbook(result, report.sheet, report.name)
        xlsx_path = output_dir / f"{report.name}.xlsx"
        output_files.append(save_xlsx(workbook, xlsx_path))

    if "csv" in report.output.formats:
        csv_path = output_dir / f"{report.name}.csv"
        output_files.append(save_csv(result, csv_path))

    emailed = False
    if report.recipients:
        subject = f"Report: {report.description or report.name}"
        body = (
            f"Attached is the '{report.name}' report, generated on "
            f"{dt.datetime.now().isoformat(timespec='seconds')}.\n\n"
            f"Rows: {result.row_count}"
        )
        send_report_email(
            recipients=report.recipients,
            subject=subject,
            body=body,
            attachments=output_files,
            dry_run=dry_run,
        )
        emailed = not dry_run

    return ReportRunResult(
        report_name=report.name,
        row_count=result.row_count,
        output_files=output_files,
        emailed=emailed,
    )


def run_all_reports(
    config: AppConfig,
    engine: Engine,
    *,
    dry_run: bool = False,
    today: dt.date | None = None,
) -> list[ReportRunResult]:
    """Run every report in the configuration, continuing after individual failures."""
    results: list[ReportRunResult] = []
    for report in config.reports:
        results.append(run_report(config, engine, report.name, dry_run=dry_run, today=today))
    return results
