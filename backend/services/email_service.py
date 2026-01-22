import os
from io import BytesIO
from pathlib import Path

import qrcode
from dotenv import load_dotenv
from fastapi import UploadFile
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

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
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr


async def send_qr_code_email(email_to: EmailStr, qr_data: str, first_name: str):
    try:
        print(f"📧 Starting to send to: {email_to}")

        qr_img = generate_qr_in_memory(qr_data)

        qr_attachment = UploadFile(file=qr_img, filename="your_qr_code.png")

        html = f"""
        <h3>Hello {first_name}!</h3>
        <p>Your employee account has been created.</p>
        <p>Your unique <b>QR Code</b> is attached.</p>
        <p>Save it on your phone or print it to be able to enter the office.</p>
        """

        message = MessageSchema(
            subject="Your QR Access Code",
            recipients=[email_to],
            body=html,
            subtype=MessageType.html,
            attachments=[qr_attachment],  #
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        print("Email was sent successfully!")

    except Exception as e:
        print(f"EMAIL SENDING ERROR: {e}")
