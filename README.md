# mysql-report-automation

[![CI](https://github.com/adriasancheza/mysql-report-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/adriasancheza/mysql-report-automation/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A small, dependable CLI that turns SQL queries into formatted Excel reports
and emails them — no notebook, no BI tool, just a YAML file and a scheduled
task.

## Why

Recurring "can you send me the monthly sales numbers" requests usually end
up as a hand-run SQL query pasted into a spreadsheet. This project replaces
that with a declarative config: define each report once (query, parameters,
formatting, recipients), then let cron or Task Scheduler run it.

## Features

- **YAML-driven reports** — name, SQL (inline or `.sql` file), parameters,
  sheet formatting, recipients, and a schedule hint, all in one file.
- **Relative date parameters** — `last_month`, `yesterday`, `this_week_start`,
  etc. resolve automatically, no hard-coded dates.
- **Any SQLAlchemy-compatible database** — MySQL via PyMySQL in production,
  SQLite for local development and tests.
- **Polished Excel output** — styled header row, auto-sized columns,
  number/date formats, frozen header, autofilter, and an optional summary
  sheet with totals.
- **Optional CSV output** alongside or instead of Excel.
- **Email delivery** over SMTP with STARTTLS and file attachments, with a
  `--dry-run` flag that builds the report but skips sending.
- **A real CLI**: `report run <name>`, `report run --all`, `report list`,
  `report validate`, structured logging, and non-zero exit codes on failure.
- **A one-minute demo** with fictional data — no MySQL server required.

## Quick start (demo, ~1 minute)

```bash
git clone https://github.com/adriasancheza/mysql-report-automation.git
cd mysql-report-automation

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"

cp .env.example .env             # Windows: copy .env.example .env
python scripts/seed_demo.py      # creates demo.db with fictional sales data

report run monthly_sales --config reports.example.yml --dry-run
report run --all --config reports.example.yml --dry-run
```

`.env.example` already points `DATABASE_URL` at the SQLite demo database
(`sqlite:///demo.db`), so the commands above work with no further setup.
Drop `--dry-run` once real SMTP credentials are in `.env` to actually send
the emails. Generated files land in `output/`.

## Using it against MySQL

1. `pip install -e .` (PyMySQL is included as a dependency).
2. In `.env`, set:
   ```
   DATABASE_URL=mysql+pymysql://user:password@host:3306/your_db
   SMTP_HOST=...
   SMTP_PORT=587
   SMTP_USERNAME=...
   SMTP_PASSWORD=...
   SMTP_FROM=reports@yourcompany.com
   ```
3. Copy `reports.example.yml` to `reports.yml` and edit it for your schema
   (queries, parameters, recipients).
4. `report validate --config reports.yml` to check the config, then
   `report run <name> --config reports.yml`.

## CLI reference

```
report list       [--config reports.yml]
report validate   [--config reports.yml]
report run <name> [--config reports.yml] [--dry-run] [--env-file .env]
report run --all  [--config reports.yml] [--dry-run] [--env-file .env]
```

Global options (before the subcommand): `--log-file logs/report.log`,
`--verbose` / `-v` for debug logging. Failures print to stderr and exit
with a non-zero code, which scheduled tasks and cron can alert on.

## Config reference

```yaml
database:
  url_env: DATABASE_URL        # env var holding the SQLAlchemy URL

output:
  directory: output            # default output directory for all reports

reports:
  - name: monthly_sales        # used on the command line: report run monthly_sales
    description: Monthly sales summary by region and product
    query_file: sql/monthly_sales.sql   # or: query: "SELECT ..."
    parameters:
      start_date: last_month_start      # see keywords below, or a literal value
      end_date: last_month_end
    sheet:
      title: Sales                      # sheet name (max 31 chars)
      freeze_header: true
      autofilter: true
      number_formats: { revenue: "#,##0.00" }
      date_formats: { order_date: "yyyy-mm-dd" }
      summary:
        enabled: true
        totals: [units, revenue]        # numeric columns totalled on a Summary sheet
    output:
      formats: [xlsx, csv]              # any of: xlsx, csv
      directory: output                 # overrides the top-level default
    recipients:
      - sales-team@example.com
    schedule: "0 7 1 * *"               # documentation only; see docs/scheduling.md
```

### Relative date parameter keywords

`today`, `yesterday`, `tomorrow`, `this_month_start`, `this_month_end`,
`last_month_start`, `last_month_end`, `next_month_start`,
`this_week_start`, `this_week_end`, `last_week_start`, `last_week_end`,
`last_7_days_start`, `last_30_days_start`, `year_start`, `year_end`,
`last_year_start`, `last_year_end`. Any other string is passed to the query
as a literal value.

## Scheduling

See [`docs/scheduling.md`](docs/scheduling.md) for Windows Task Scheduler
(`schtasks`) and cron examples.

## Security notes

- **Never commit `.env`** — it's gitignored; only `.env.example` (with
  placeholder values) is tracked.
- **Never commit real report output or company data.** `reports.yml` (your
  real config) is not tracked; only `reports.example.yml` with fictional
  data is.
- Queries are parameterised through SQLAlchemy (`:param` placeholders) —
  never string-format user input into SQL.
- SMTP credentials are read from the environment only; consider an app
  password or a dedicated mail-sending account, not a personal inbox
  password.
- Run the process as a low-privilege OS/service account with read-only
  database access where possible.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

CI runs `ruff` and `pytest` on Python 3.12 and 3.13 for every push and pull
request (`.github/workflows/ci.yml`).

## License

[MIT](LICENSE) © 2026 Adrià Sánchez
