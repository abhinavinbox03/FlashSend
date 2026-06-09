"""FastAPI backend for sending emails with PDF attachments."""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from email_service import is_valid_email, send_email

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_ATTACHMENT = BASE_DIR / "attachments" / "sample.pdf"
DEFAULT_BODY_FILE = BASE_DIR / "message.txt"

app = FastAPI(title="Email Sender API", version="1.0.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5500")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://127.0.0.1:5500", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SendEmailRequest(BaseModel):
    email: EmailStr = Field(..., description="Recipient email address")


class SendEmailResponse(BaseModel):
    success: bool
    message: str


def load_body() -> str:
    body_file = Path(os.getenv("BODY_FILE", str(DEFAULT_BODY_FILE)))

    if not body_file.is_file():
        raise HTTPException(
            status_code=500,
            detail=f"Email body file not found: {body_file}",
        )

    return body_file.read_text(encoding="utf-8")


def get_config() -> dict:
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")

    if not smtp_user or not smtp_password:
        raise HTTPException(
            status_code=500,
            detail="Server email credentials are not configured.",
        )

    attachment = os.getenv("ATTACHMENT_PATH", str(DEFAULT_ATTACHMENT))

    return {
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": smtp_user,
        "smtp_password": smtp_password,
        "sender_name": os.getenv("SENDER_NAME", ""),
        "subject": os.getenv("DEFAULT_SUBJECT", "Your document"),
        "body": load_body(),
        "attachment_path": attachment if os.path.isfile(attachment) else None,
    }


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/send-email", response_model=SendEmailResponse)
@limiter.limit("50/hour")
def send_email_endpoint(request: Request, payload: SendEmailRequest) -> SendEmailResponse:
    recipient = str(payload.email).strip().lower()

    if not is_valid_email(recipient):
        raise HTTPException(status_code=400, detail="Invalid email address.")

    config = get_config()

    try:
        send_email(
            smtp_host=config["smtp_host"],
            smtp_port=config["smtp_port"],
            smtp_user=config["smtp_user"],
            smtp_password=config["smtp_password"],
            sender_name=config["sender_name"],
            recipient=recipient,
            subject=config["subject"],
            body=config["body"],
            attachment_path=config["attachment_path"],
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to send email: {exc}") from exc

    return SendEmailResponse(
        success=True,
        message=f"Email sent successfully to {recipient}.",
    )
