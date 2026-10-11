"""Optional SMTP email for OTP codes.

When SMTP_HOST/SMTP_USER/SMTP_PASS env vars are absent the demo behaviour is
unchanged (codes are returned to the UI as dev_otp). When present, codes are
emailed and never leaked in API responses.
"""
import os
import smtplib
from email.message import EmailMessage

SUBJECTS = {"signup": "Verify your Skillhub account",
             "reset": "Skillhub password reset code",
             "payment": "Skillhub payment verification code"}


def enabled():
    return all(os.environ.get(k) for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS"))


def send_otp(to_email, code, purpose):
    """Best effort: True when the email was handed to the SMTP server."""
    if not enabled():
        return False
    subject = SUBJECTS.get(purpose, "Skillhub verification code")
    body = ("Your Skillhub code is %s (valid for 5 minutes).\n\n"
            "If you did not request it, you can safely ignore this email."
            % code)
    try:
        msg = EmailMessage()
        msg["From"] = os.environ.get("SMTP_FROM") or os.environ["SMTP_USER"]
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)
        port = int(os.environ.get("SMTP_PORT", "587"))
        with smtplib.SMTP(os.environ["SMTP_HOST"], port, timeout=10) as s:
            s.starttls()
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(msg)
        return True
    except Exception:
        return False