"""
Async email sender.

If SMTP is not configured (settings.smtp.enabled is False), falls back to
logging the message — convenient during local development.
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from core.config import settings

log = logging.getLogger(__name__)


async def send_email(*, to: str, subject: str, html_body: str) -> None:
    if not settings.smtp.enabled:
        log.warning(
            "SMTP disabled — email NOT sent to %s | subject=%s | body=%s",
            to,
            subject,
            html_body,
        )
        return

    message = MIMEMultipart("alternative")
    message["From"] = settings.smtp.from_address
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))

    await aiosmtplib.send(
        message,
        hostname=settings.smtp.host,
        port=settings.smtp.port,
        username=settings.smtp.username,
        password=settings.smtp.password,
        start_tls=settings.smtp.use_tls,
    )


async def send_verification_email(to: str, token: str) -> None:
    await send_email(
        to=to,
        subject="Verify your Bank account",
        html_body=f"""
        <h2>Welcome to Bank</h2>
        <p>Please verify your email address to activate your account.</p>
        <p>Use this token to call <code>POST /api/v1/auth/verify</code>:</p>
        <pre><code>{token}</code></pre>
        <p>The token expires in 1 hour.</p>
        <p>If you did not register, please ignore this email.</p>
        """,
    )


async def send_password_reset_email(to: str, token: str) -> None:
    await send_email(
        to=to,
        subject="Reset your Bank account password",
        html_body=f"""
        <h2>Password Reset</h2>
        <p>You requested a password reset for your Bank account.</p>
        <p>Use this token to call <code>POST /api/v1/auth/reset-password</code>:</p>
        <pre><code>{token}</code></pre>
        <p>The token expires in 1 hour.</p>
        <p>If you did not request this, please ignore this email.</p>
        """,
    )
