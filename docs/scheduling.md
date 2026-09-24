# Scheduling

`report` itself does not run a scheduler — it is a single command you run
once. Use your OS scheduler to trigger it on the cadence in each report's
`schedule` field (that field is documentation only; the OS scheduler is the
source of truth for timing).

## Linux / macOS: cron

Edit the crontab for the user that should run reports:

```bash
crontab -e
```

Example: run the monthly sales report at 07:00 on the 1st of the month, and
the daily orders report every day at 06:00.

```cron
0 7 1 * *  cd /opt/mysql-report-automation && .venv/bin/report run monthly_sales --config reports.yml >> logs/cron.log 2>&1
0 6 * * *  cd /opt/mysql-report-automation && .venv/bin/report run daily_orders --config reports.yml >> logs/cron.log 2>&1
```

Or run everything nightly:

```cron
0 5 * * *  cd /opt/mysql-report-automation && .venv/bin/report run --all --config reports.yml >> logs/cron.log 2>&1
```

Make sure `.env` is readable by the cron user, or set `DATABASE_URL` /
`SMTP_*` directly in the crontab / a wrapper script.

## Windows: Task Scheduler

Create a scheduled task with `schtasks` (run from an elevated prompt, adjust
paths for your install):

```powershell
schtasks /Create /SC MONTHLY /D 1 /TN "MySQLReports_MonthlySales" /TR "C:\apps\mysql-report-automation\.venv\Scripts\report.exe run monthly_sales --config C:\apps\mysql-report-automation\reports.yml" /ST 07:00

schtasks /Create /SC DAILY /TN "MySQLReports_DailyOrders" /TR "C:\apps\mysql-report-automation\.venv\Scripts\report.exe run daily_orders --config C:\apps\mysql-report-automation\reports.yml" /ST 06:00
```

To run every report each night:

```powershell
schtasks /Create /SC DAILY /TN "MySQLReports_All" /TR "C:\apps\mysql-report-automation\.venv\Scripts\report.exe run --all --config C:\apps\mysql-report-automation\reports.yml" /ST 05:00
```

List or remove tasks with:

```powershell
schtasks /Query /TN "MySQLReports_All"
schtasks /Delete /TN "MySQLReports_All" /F
```

The scheduled task's working directory determines where `.env` is loaded
from (via `python-dotenv`) unless you pass `--env-file`. Use a wrapper
`.bat`/`.ps1` script that `cd`s into the project directory first if needed.
