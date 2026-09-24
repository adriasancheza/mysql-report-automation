from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mysql_report_automation.cli import app

runner = CliRunner()


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "reports.yml"
    config_path.write_text(
        "database:\n"
        "  url_env: DATABASE_URL\n"
        "output:\n"
        "  directory: output\n"
        "reports:\n"
        "  - name: north_orders\n"
        "    description: North region orders\n"
        "    query: |\n"
        "      SELECT region, order_date, units, revenue FROM orders\n"
        "      WHERE region = :region ORDER BY order_date\n"
        "    parameters:\n"
        "      region: North\n"
        "    sheet:\n"
        "      title: North\n"
        "    output:\n"
        "      formats: [xlsx, csv]\n"
        "    recipients:\n"
        "      - team@example.com\n",
        encoding="utf-8",
    )
    return config_path


def test_list_command(sqlite_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = _write_config(tmp_path)

    result = runner.invoke(app, ["--log-file", "logs/test.log", "list", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "north_orders" in result.stdout


def test_validate_command(sqlite_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = _write_config(tmp_path)

    result = runner.invoke(
        app, ["--log-file", "logs/test.log", "validate", "--config", str(config_path)]
    )

    assert result.exit_code == 0
    assert "OK" in result.stdout


def test_run_dry_run_writes_output(sqlite_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = _write_config(tmp_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{sqlite_db}")

    result = runner.invoke(
        app,
        [
            "--log-file",
            "logs/test.log",
            "run",
            "north_orders",
            "--config",
            str(config_path),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "output" / "north_orders.xlsx").exists()
    assert (tmp_path / "output" / "north_orders.csv").exists()


def test_run_requires_name_or_all(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = _write_config(tmp_path)

    result = runner.invoke(app, ["--log-file", "logs/test.log", "run", "--config", str(config_path)])

    assert result.exit_code == 2


def test_run_unknown_report_fails(sqlite_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = _write_config(tmp_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{sqlite_db}")

    result = runner.invoke(
        app,
        ["--log-file", "logs/test.log", "run", "does_not_exist", "--config", str(config_path), "--dry-run"],
    )

    assert result.exit_code == 1
