from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mysql_report_automation.email_sender import (
    EmailError,
    SmtpSettings,
    build_message,
    send_report_email,
)


def test_dry_run_does_not_touch_smtp(caplog):
    with patch("smtplib.SMTP") as smtp_cls:
        send_report_email(
            recipients=["a@example.com"],
            subject="Test",
            body="Body",
            dry_run=True,
        )
        smtp_cls.assert_not_called()


def test_no_recipients_skips_send():
    with patch("smtplib.SMTP") as smtp_cls:
        send_report_email(recipients=[], subject="Test", body="Body", dry_run=False)
        smtp_cls.assert_not_called()


def test_build_message_includes_attachment(tmp_path):
    attachment = tmp_path / "report.csv"
    attachment.write_text("a,b\n1,2\n", encoding="utf-8")

    msg = build_message(
        sender="reports@example.com",
        recipients=["team@example.com"],
        subject="Subj",
        body="Hello",
        attachments=[attachment],
    )

    assert msg["From"] == "reports@example.com"
    assert msg["To"] == "team@example.com"
    assert msg["Subject"] == "Subj"
    filenames = [part.get_filename() for part in msg.iter_attachments()]
    assert "report.csv" in filenames


def test_send_report_email_uses_starttls_and_login():
    settings = SmtpSettings(
        host="smtp.example.com",
        port=587,
        username="user",
        password="pass",
        sender="reports@example.com",
        use_tls=True,
    )
    mock_smtp = MagicMock()
    mock_smtp.__enter__.return_value = mock_smtp

    with patch("smtplib.SMTP", return_value=mock_smtp) as smtp_cls:
        send_report_email(
            recipients=["a@example.com"],
            subject="Test",
            body="Body",
            settings=settings,
            dry_run=False,
        )

    smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=30)
    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("user", "pass")
    mock_smtp.send_message.assert_called_once()


def test_send_report_email_wraps_smtp_errors():
    settings = SmtpSettings(
        host="smtp.example.com",
        port=587,
        username=None,
        password=None,
        sender="reports@example.com",
    )
    mock_smtp = MagicMock()
    mock_smtp.__enter__.side_effect = OSError("connection refused")

    with patch("smtplib.SMTP", return_value=mock_smtp), pytest.raises(EmailError):
        send_report_email(
            recipients=["a@example.com"], subject="Test", body="Body", settings=settings
        )


def test_smtp_settings_from_env_requires_host(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    with pytest.raises(EmailError):
        SmtpSettings.from_env()
