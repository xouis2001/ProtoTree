import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

from app.core.config import settings


def send_reset_email(to_email: str, reset_url: str) -> None:
    """Send password-reset email via QQ SMTP (SSL 465). Raises on failure."""
    subject = "Lu Lab 密码重置 / Password Reset"
    body = (
        f"您好，\n\n您（或他人）请求重置 Lu Lab 账号密码。\n"
        f"请在 30 分钟内点击以下链接完成重置：\n\n{reset_url}\n\n"
        f"若非本人操作，请忽略此邮件，密码不会被更改。\n\n— Lu Lab"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header(settings.smtp_from_name, "utf-8")), settings.smtp_user))
    msg["To"] = to_email

    with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_user, [to_email], msg.as_string())
