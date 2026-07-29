import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from html import escape
from typing import Any

from app.core.config import settings


def _send_html(to_email: str, subject: str, html: str) -> None:
    """Send one HTML email. Raises so the outbox worker can retry safely."""
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header(settings.smtp_from_name, "utf-8")), settings.smtp_user))
    msg["To"] = to_email
    with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_user, [to_email], msg.as_string())


def send_reset_email(to_email: str, reset_url: str) -> None:
    _send_html(
        to_email,
        "Lu Lab 密码重置",
        f'<p>您好，</p><p>请点击以下链接重置密码（30 分钟内有效）：</p><p><a href="{escape(reset_url, quote=True)}">重置密码</a></p><p>如果不是您本人操作，请忽略此邮件。</p>',
    )


def send_templated_email(to_email: str, template: str, payload: dict[str, Any]) -> None:
    """Render the small, allow-listed transactional template set."""
    name = escape(str(payload.get("name", "申请人")))
    email = escape(str(payload.get("email", "")))
    if template == "registration_submitted_admin":
        url = escape(settings.admin_approval_url, quote=True)
        _send_html(
            to_email,
            "Lu Lab：新的注册申请待审批",
            f"<p>管理员您好，</p><p><strong>{name}</strong>（{email}）已完成头像并提交注册申请。</p><p><a href=\"{url}\">前往审批后台</a></p>",
        )
        return
    if template == "registration_approved_user":
        url = escape(settings.login_url, quote=True)
        _send_html(
            to_email,
            "Lu Lab：您的注册申请已通过",
            f"<p>{name}，您好：</p><p>您的注册申请已通过审批，现在可以登录。</p><p><a href=\"{url}\">直接登录</a></p>",
        )
        return
    raise ValueError(f"Unknown email template: {template}")
