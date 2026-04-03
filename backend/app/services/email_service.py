from __future__ import annotations

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

import aiosmtplib
from jinja2 import Environment, PackageLoader, select_autoescape

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.digest import DailyDigest
    from app.models.paper import Paper
    from app.models.user import User

logger = logging.getLogger(__name__)

_DIGEST_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Your PaperNosh Digest</title></head>
<body style="font-family:sans-serif;max-width:680px;margin:0 auto;padding:20px;">
  <h1 style="color:#2563eb;">📄 Your Daily PaperNosh Digest</h1>
  <p>Hello {{ user.full_name or user.email }},</p>
  <p>Here are your top papers for {{ digest.date.strftime('%B %d, %Y') }}:</p>
  {% for entry in papers %}
  <div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin-bottom:16px;">
    <h3 style="margin:0 0 8px;"><a href="{{ entry.url }}" style="color:#1d4ed8;text-decoration:none;">{{ entry.title }}</a></h3>
    <p style="color:#6b7280;margin:4px 0;font-size:14px;">
      {{ entry.authors|map(attribute='name')|join(', ') }}
      {% if entry.journal_name %} &bull; <em>{{ entry.journal_name }}</em>{% endif %}
      {% if entry.published_date %} &bull; {{ entry.published_date }}{% endif %}
    </p>
    {% if entry.abstract %}
    <p style="font-size:14px;color:#374151;margin-top:8px;">{{ entry.abstract[:300] }}{% if entry.abstract|length > 300 %}…{% endif %}</p>
    {% endif %}
    {% if entry.ai_summary %}
    <div style="background:#f0f9ff;border-left:3px solid #2563eb;padding:8px 12px;margin-top:8px;font-size:13px;color:#1e40af;">
      <strong>AI Summary:</strong> {{ entry.ai_summary }}
    </div>
    {% endif %}
  </div>
  {% endfor %}
  <hr>
  <p style="font-size:12px;color:#9ca3af;">You are receiving this because you signed up for PaperNosh.
  <a href="https://papernosh.io/unsubscribe">Unsubscribe</a></p>
</body>
</html>
"""


class EmailService:
    async def send_digest_email(
        self,
        user: "User",
        digest: "DailyDigest",
        papers: list["Paper"],
    ) -> bool:
        if not settings.SMTP_HOST:
            logger.warning("SMTP not configured, skipping email for user %s", user.id)
            return False

        html_body = _render_template(user, digest, papers)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📄 Your PaperNosh Digest – {digest.date}"
        msg["From"] = settings.FROM_EMAIL
        msg["To"] = user.email
        msg.attach(MIMEText(html_body, "html"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER or None,
                password=settings.SMTP_PASSWORD or None,
                start_tls=True,
            )
            logger.info("Digest email sent to %s", user.email)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to send email to %s: %s", user.email, exc, exc_info=True)
            return False


def _render_template(
    user: "User", digest: "DailyDigest", papers: list["Paper"]
) -> str:
    from jinja2 import BaseLoader, Environment

    env = Environment(loader=BaseLoader(), autoescape=True)
    tmpl = env.from_string(_DIGEST_TEMPLATE)
    return tmpl.render(user=user, digest=digest, papers=papers)
