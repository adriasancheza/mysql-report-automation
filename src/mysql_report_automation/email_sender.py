"""Send report emails over SMTP with STARTTLS, with attachments and dry-run support."""

from __future__ import annotations

import logging
import mimetypes
import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Raised when SMTP configuration is missing or sending fails."""


@dataclass
class SmtpSettings:
    host: str
    port: int
    username: str | None
    password: str | None
    sender: str
    use_tls: bool = True

    @classmethod
    def from_env(cls) -> SmtpSettings:
        host = os.environ.get("SMTP_HOST")
        if not host:
            raise EmailError(
                "SMTP_HOST is not set. Copy .env.example to .env and configure SMTP settings."
            )
        port = int(os.environ.get("SMTP_PORT", "587"))
        username = os.environ.get("SMTP_USERNAME") or None
        password = os.environ.get("SMTP_PASSWORD") or None
        sender = os.environ.get("SMTP_FROM", username or "reports@example.com")
        use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() not in ("0", "false", "no")
        return cls(
            host=host, port=port, username=username, password=password, sender=sender, use_tls=use_tls
        )


def build_message(
    *,
    sender: str,
    recipients: list[str],
    subject: str,
    body: str,
    attachments: list[Path] | None = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    for path in attachments or []:
        path = Path(path)
        data = path.read_bytes()
        mime_type, _ = mimetypes.guess_type(path.name)
        maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=path.name)

    return msg


def send_report_email(
    *,
    recipients: list[str],
    subject: str,
    body: str,
    attachments: list[Path] | None = None,
    settings: SmtpSettings | None = None,
    dry_run: bool = False,
) -> None:
    """Send an email with the given attachments. No-op (logged) when dry_run is True."""
    if not recipients:
        logger.warning("No recipients configured; skipping email send.")
        return

    if dry_run:
        logger.info(
            "[dry-run] Would send email to %s with subject '%s' and %d attachment(s)",
            recipients,
            subject,
            len(attachments or []),
        )
        return

    settings = settings or SmtpSettings.from_env()
    message = build_message(
        sender=settings.sender,
        recipients=recipients,
        subject=subject,
        body=body,
        attachments=attachments,
    )

    try:
        with smtplib.SMTP(settings.host, settings.port, timeout=30) as smtp:
            smtp.ehlo()
            if settings.use_tls:
                smtp.starttls()
                smtp.ehlo()
            if settings.username and settings.password:
                smtp.login(settings.username, settings.password)
            smtp.send_message(message)
    except Exception as exc:
        raise EmailError(f"Failed to send email: {exc}") from exc

    logger.info("Sent report email to %s", recipients)
