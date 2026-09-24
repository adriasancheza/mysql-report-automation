"""Command-line interface for mysql-report-automation.

Commands:
    report run <name>        Run a single report by name.
    report run --all         Run every report defined in the config.
    report list               List reports defined in the config.
    report validate           Validate the config without running anything.
"""

from __future__ import annotations

import logging

import typer
from dotenv import load_dotenv

from mysql_report_automation.config import ConfigError, load_config, validate_config
from mysql_report_automation.db import DatabaseError, get_database_url, get_engine
from mysql_report_automation.logging_config import setup_logging
from mysql_report_automation.runner import run_all_reports, run_report

app = typer.Typer(
    name="report",
    help="Turn SQL queries into scheduled, formatted Excel reports and email them.",
    add_completion=False,
    no_args_is_help=True,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = "reports.yml"


def _load_env(env_file: str | None) -> None:
    if env_file:
        load_dotenv(env_file, override=True)
    else:
        load_dotenv(override=False)


@app.callback()
def main(
    log_file: str = typer.Option("logs/report.log", help="Path to the log file."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging."),
) -> None:
    """Shared setup: logging configuration."""
    setup_logging(log_file, level=logging.DEBUG if verbose else logging.INFO)


@app.command("list")
def list_reports(
    config: str = typer.Option(DEFAULT_CONFIG, "--config", "-c", help="Path to the YAML config."),
) -> None:
    """List all reports defined in the configuration file."""
    try:
        cfg = load_config(config)
    except ConfigError as exc:
        typer.secho(f"Config error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    for report in cfg.reports:
        recipients = ", ".join(report.recipients) or "(none)"
        typer.echo(f"- {report.name}: {report.description or '(no description)'}")
        typer.echo(f"    schedule: {report.schedule or '(none)'}  recipients: {recipients}")


@app.command("validate")
def validate(
    config: str = typer.Option(DEFAULT_CONFIG, "--config", "-c", help="Path to the YAML config."),
) -> None:
    """Validate the configuration file (queries resolve, formats are supported, etc.)."""
    try:
        cfg = load_config(config)
    except ConfigError as exc:
        typer.secho(f"Config error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    errors = validate_config(cfg)
    if errors:
        typer.secho(f"Found {len(errors)} problem(s):", fg=typer.colors.RED, err=True)
        for err in errors:
            typer.secho(f"  - {err}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.secho(f"OK: {len(cfg.reports)} report(s) valid.", fg=typer.colors.GREEN)


@app.command("run")
def run(
    name: str = typer.Argument(None, help="Report name to run. Omit when using --all."),
    all_reports: bool = typer.Option(False, "--all", help="Run every report in the config."),
    config: str = typer.Option(DEFAULT_CONFIG, "--config", "-c", help="Path to the YAML config."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Build reports but skip sending email."
    ),
    env_file: str = typer.Option(None, "--env-file", help="Path to a .env file to load."),
) -> None:
    """Run one report (by name) or every report with --all."""
    if not name and not all_reports:
        typer.secho("Provide a report name, or pass --all.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)
    if name and all_reports:
        typer.secho("Pass either a report name or --all, not both.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    _load_env(env_file)

    try:
        cfg = load_config(config)
    except ConfigError as exc:
        typer.secho(f"Config error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    try:
        db_url = get_database_url(cfg.database_url_env)
        engine = get_engine(db_url)
    except DatabaseError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    try:
        if all_reports:
            results = run_all_reports(cfg, engine, dry_run=dry_run)
        else:
            results = [run_report(cfg, engine, name, dry_run=dry_run)]
    except (ConfigError, DatabaseError) as exc:
        typer.secho(f"Run failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # noqa: BLE001 - surface unexpected failures with a clean exit code
        logger.exception("Unexpected error while running report(s)")
        typer.secho(f"Unexpected error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    for result in results:
        files = ", ".join(str(p) for p in result.output_files) or "(none)"
        typer.secho(
            f"OK  {result.report_name}: {result.row_count} row(s) -> {files}"
            f"{' (emailed)' if result.emailed else ''}",
            fg=typer.colors.GREEN,
        )


def main_entry() -> None:
    """Console-script entry point (declared in pyproject.toml)."""
    app()


if __name__ == "__main__":
    main_entry()
