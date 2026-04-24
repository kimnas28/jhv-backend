import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def _truncate_password(password: str) -> str:
    """
    Truncate password to 72 bytes (bcrypt's limit).
    Bcrypt has a hard limit of 72 bytes. Longer passwords are silently truncated,
    which can cause authentication mismatches if not handled consistently.
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return password_bytes.decode('utf-8', errors='ignore')

def get_password_hash(password):
    """Hash password with bcrypt, handling the 72-byte limit."""
    truncated_password = _truncate_password(password)
    return pwd_context.hash(truncated_password)

def verify_password(plain_password, hashed_password):
    """Verify password with bcrypt, handling the 72-byte limit."""
    truncated_password = _truncate_password(plain_password)
    return pwd_context.verify(truncated_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt