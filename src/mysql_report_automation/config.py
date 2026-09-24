"""Load and validate the YAML report configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised when the configuration file is missing, malformed, or invalid."""


@dataclass
class SummaryConfig:
    enabled: bool = False
    totals: list[str] = field(default_factory=list)


@dataclass
class SheetConfig:
    title: str = "Report"
    freeze_header: bool = True
    autofilter: bool = True
    number_formats: dict[str, str] = field(default_factory=dict)
    date_formats: dict[str, str] = field(default_factory=dict)
    summary: SummaryConfig = field(default_factory=SummaryConfig)


@dataclass
class OutputConfig:
    formats: list[str] = field(default_factory=lambda: ["xlsx"])
    directory: str = "output"


@dataclass
class ReportConfig:
    name: str
    description: str = ""
    query: str | None = None
    query_file: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    sheet: SheetConfig = field(default_factory=SheetConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    recipients: list[str] = field(default_factory=list)
    schedule: str | None = None

    def resolve_query(self, base_dir: Path) -> str:
        """Return the SQL text for this report, reading ``query_file`` if needed."""
        if self.query:
            return self.query
        if self.query_file:
            sql_path = (base_dir / self.query_file).resolve()
            if not sql_path.is_file():
                raise ConfigError(
                    f"Report '{self.name}': query_file '{self.query_file}' not found "
                    f"(resolved to {sql_path})"
                )
            return sql_path.read_text(encoding="utf-8")
        raise ConfigError(f"Report '{self.name}': must define either 'query' or 'query_file'")


@dataclass
class AppConfig:
    database_url_env: str = "DATABASE_URL"
    output: OutputConfig = field(default_factory=OutputConfig)
    reports: list[ReportConfig] = field(default_factory=list)
    base_dir: Path = field(default_factory=Path.cwd)

    def get_report(self, name: str) -> ReportConfig:
        for report in self.reports:
            if report.name == name:
                return report
        available = ", ".join(r.name for r in self.reports) or "(none)"
        raise ConfigError(f"Report '{name}' not found. Available reports: {available}")


def _build_summary(raw: dict[str, Any] | None) -> SummaryConfig:
    raw = raw or {}
    return SummaryConfig(
        enabled=bool(raw.get("enabled", False)),
        totals=list(raw.get("totals", [])),
    )


def _build_sheet(raw: dict[str, Any] | None) -> SheetConfig:
    raw = raw or {}
    return SheetConfig(
        title=raw.get("title", "Report"),
        freeze_header=bool(raw.get("freeze_header", True)),
        autofilter=bool(raw.get("autofilter", True)),
        number_formats=dict(raw.get("number_formats", {})),
        date_formats=dict(raw.get("date_formats", {})),
        summary=_build_summary(raw.get("summary")),
    )


def _build_output(raw: dict[str, Any] | None, default_directory: str = "output") -> OutputConfig:
    raw = raw or {}
    return OutputConfig(
        formats=list(raw.get("formats", ["xlsx"])),
        directory=raw.get("directory", default_directory),
    )


def _build_report(raw: dict[str, Any], default_output_dir: str) -> ReportConfig:
    if "name" not in raw:
        raise ConfigError(f"Report entry missing required 'name' field: {raw}")
    return ReportConfig(
        name=raw["name"],
        description=raw.get("description", ""),
        query=raw.get("query"),
        query_file=raw.get("query_file"),
        parameters=dict(raw.get("parameters", {})),
        sheet=_build_sheet(raw.get("sheet")),
        output=_build_output(raw.get("output"), default_output_dir),
        recipients=list(raw.get("recipients", [])),
        schedule=raw.get("schedule"),
    )


def load_config(path: str | Path) -> AppConfig:
    """Load and parse a reports YAML configuration file."""
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"Configuration file not found: {path}")

    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    database_raw = raw.get("database", {}) or {}
    database_url_env = database_raw.get("url_env", "DATABASE_URL")

    default_output = _build_output(raw.get("output"))

    reports_raw = raw.get("reports", [])
    if not isinstance(reports_raw, list) or not reports_raw:
        raise ConfigError("Configuration must define a non-empty 'reports' list")

    reports = [_build_report(r, default_output.directory) for r in reports_raw]

    names = [r.name for r in reports]
    duplicates = {n for n in names if names.count(n) > 1}
    if duplicates:
        raise ConfigError(f"Duplicate report names in config: {', '.join(sorted(duplicates))}")

    return AppConfig(
        database_url_env=database_url_env,
        output=default_output,
        reports=reports,
        base_dir=path.parent.resolve(),
    )


def validate_config(config: AppConfig) -> list[str]:
    """Return a list of human-readable validation problems (empty if valid)."""
    errors: list[str] = []
    for report in config.reports:
        try:
            report.resolve_query(config.base_dir)
        except ConfigError as exc:
            errors.append(str(exc))
        if report.sheet.summary.enabled and not report.sheet.summary.totals:
            errors.append(
                f"Report '{report.name}': summary.enabled is true but no 'totals' columns listed"
            )
        if report.output.formats:
            unknown = [f for f in report.output.formats if f not in ("xlsx", "csv")]
            if unknown:
                errors.append(
                    f"Report '{report.name}': unsupported output format(s) {unknown} "
                    "(supported: xlsx, csv)"
                )
    return errors
