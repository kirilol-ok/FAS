import os
from io import BytesIO
from pathlib import Path

import qrcode
from dotenv import load_dotenv
from fastapi import UploadFile
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

# Load .env from backend/.env (repo layout: backend/services/email_service.py)
backend_dir = Path(__file__).resolve().parent
root_dir = backend_dir.parent
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path)

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM", ""),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


def generate_qr_in_memory(data: str) -> BytesIO:
    """Generate a QR code PNG into an in-memory BytesIO buffer."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


async def send_qr_code_email(email_to: EmailStr, qr_data: str, first_name: str):
    """
    Send an email with a QR code attached.

    NOTE:
    FastAPI's UploadFile __init__ signature is:
        UploadFile(file, *, size=None, filename=None, headers=None)
    It does NOT accept content_type as a kwarg; content_type is derived from headers.
    """
    try:
        print(f"📧 Starting to send to: {email_to}")

        qr_img = generate_qr_in_memory(qr_data)

        # Provide content type through headers so UploadFile.content_type is available.
        headers = None
        try:
            from starlette.datastructures import Headers  # type: ignore
            headers = Headers({"content-type": "image/png"})
        except Exception:
            headers = {"content-type": "image/png"}

        qr_attachment = UploadFile(
            file=qr_img,
            filename="your_qr_code.png",
            headers=headers,
        )

        html = f"""
        <h3>Cześć {first_name}!</h3>
        <p>Twoje konto pracownika zostało utworzone.</p>
        <p>Twój unikalny <b>kod QR</b> znajduje się w załączniku.</p>
        <p>Zapisz go w telefonie lub wydrukuj, aby móc wejść do biura.</p>
        """

        message = MessageSchema(
            subject="Twój Kod Dostępu QR",
            recipients=[email_to],
            body=html,
            subtype=MessageType.html,
            attachments=[qr_attachment],
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        print("✅ Email was sent successfully!")

    except Exception as e:
        print(f"EMAIL SENDING ERROR: {e}")
