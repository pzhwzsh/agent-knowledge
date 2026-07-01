from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class NotificationResult:
    status: str
    message: str


class EmailNotifier:
    def send(self, *, to_email: str, subject: str, body: str) -> NotificationResult:
        settings = get_settings()
        if not settings.smtp_user or not settings.smtp_password or not settings.smtp_from:
            return NotificationResult(status="skipped", message="SMTP is not configured.")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.smtp_from
        message["To"] = to_email
        message.set_content(body)

        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
        return NotificationResult(status="sent", message="Email sent.")


class DingTalkNotifier:
    def send(self, *, webhook: str, text: str) -> NotificationResult:
        if not webhook:
            return NotificationResult(status="skipped", message="DingTalk webhook is not configured.")
        response = httpx.post(webhook, json={"msgtype": "text", "text": {"content": text}}, timeout=10)
        response.raise_for_status()
        return NotificationResult(status="sent", message="DingTalk message sent.")
