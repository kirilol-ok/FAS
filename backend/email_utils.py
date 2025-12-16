# backend/email_utils.py
import os
from io import BytesIO
from pathlib import Path

import qrcode
from dotenv import load_dotenv
from fastapi import UploadFile
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

# --- 1. load env ---

# take backend path
backend_dir = Path(__file__).resolve().parent
# take one folf=der up path
root_dir = backend_dir.parent
# find env
env_path = root_dir / ".env"

# load file
load_dotenv(dotenv_path=env_path)

# --- 2. configuration ---
conf = ConnectionConfig(
    # more argument to avoid none mistakes
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM", ""),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# --- 2. genetae qr ---
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
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# --- 3. email send ---
async def send_qr_code_email(email_to: EmailStr, qr_data: str, first_name: str):
    try:
        print(f"📧 Rozpoczynam wysyłkę do: {email_to}")
        
        # 1. genetare qr
        qr_img = generate_qr_in_memory(qr_data)
        
        # 2. upload qr file
        qr_attachment = UploadFile(
            file=qr_img, 
            filename="twoj_kod_qr.png"
        )

        html = f"""
        <h3>Witaj {first_name}!</h3>
        <p>Twoje konto pracownicze zostało utworzone.</p>
        <p>W załączniku znajduje się Twój unikalny <b>Kod QR</b>.</p>
        <p>Zapisz go w telefonie lub wydrukuj, aby móc wejść do biura.</p>
        """

        message = MessageSchema(
            subject="Twój Kod Dostępu QR",
            recipients=[email_to],
            body=html,
            subtype=MessageType.html,
            attachments=[qr_attachment]  # 
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        print("E-mail został wysłany poprawnie!")
        
    except Exception as e:
        print(f"BŁĄD WYSYŁKI EMAILA: {e}")