import os
from datetime import datetime, timedelta, timezone
import bcrypt
from dotenv import load_dotenv
from jose import jwt
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not configured")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET not configured")

def get_conn():
	return psycopg2.connect(DATABASE_URL)


def hash_password(password: str) -> str:
	pwd_bytes = password.encode('utf-8')
	salt = bcrypt.gensalt()
	hashed = bcrypt.hashpw(pwd_bytes, salt)
	return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        plain.encode('utf-8'), 
        hashed.encode('utf-8')
    )


def create_access_token(subject: str, expires_hours: int = 24) -> str:
	now = datetime.now(timezone.utc)
	payload = {
        "sub": subject, 
        "iat": now,
        "exp": now + timedelta(hours=expires_hours)
    }
	token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
	return token
