"""Send a single email with an optional PDF attachment via SMTP."""

import os
import re
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip()))


def load_attachment(path: str) -> tuple[str, bytes]:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Attachment not found: {path}")

    with open(path, "rb") as f:
        data = f.read()

    return os.path.basename(path), data


def send_email(
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    sender_name: str,
    recipient: str,
    subject: str,
    body: str,
    attachment_path: str | None = None,
) -> None:
    msg = MIMEMultipart()
    msg["From"] = f"{sender_name} <{smtp_user}>" if sender_name else smtp_user
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if attachment_path:
        filename, data = load_attachment(attachment_path)
        part = MIMEBase("application", "pdf")
        part.set_payload(data)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.sendmail(smtp_user, [recipient], msg.as_strin())
