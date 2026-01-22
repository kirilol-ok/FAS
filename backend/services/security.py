from passlib.context import CryptContext

# Konfiguracja kontekstu hashowania (używamy algorytmu bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Sprawdza czy podane hasło pasuje do hasha w bazie"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generuje hash z hasła"""
    return pwd_context.hash(password)