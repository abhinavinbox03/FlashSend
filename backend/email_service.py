import os
import re
import base64
import requests

EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def is_valid_email(email):
    return bool(EMAIL_PATTERN.match(email.strip()))


def load_attachment(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)

    with open(path, "rb") as f:
        return os.path.basename(path), f.read()


def send_email(
    *,
    api_key,
    from_email,
    recipient,
    subject,
    body,
    attachment_path=None,
):

    payload = {
        "from": from_email,
        "to": [recipient],
        "subject": subject,
        "text": body,
    }

    if attachment_path:
        filename, data = load_attachment(attachment_path)

        payload["attachments"] = [{
            "filename": filename,
            "content": base64.b64encode(data).decode(),
        }]

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    print(response.status_code)
    print(response.text)

    if response.status_code >= 300:
        raise Exception(response.text)