import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import sql
from psycopg2.errors import UniqueViolation
from auth_utils import get_conn, hash_password, verify_password, create_access_token

load_dotenv()

app = FastAPI(title="Auth Service")

class RegisterRequest(BaseModel):
	email: EmailStr
	password: str


class LoginRequest(BaseModel):
	email: EmailStr
	password: str


def insert_user(email: str, password_hash: str):
	conn = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute(
			"INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id, email",
			(email, password_hash),
		)
		row = cur.fetchone()
		conn.commit()
		cur.close()
		return row
	except Exception as e:
		print(f"✗ DB Error: {e}")
		return None
	finally:
		if conn:
			conn.close()


def fetch_user_by_email(email: str):
	conn = None
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute(
			"SELECT id, email, password_hash FROM users WHERE email = %s",
			(email,)
		)
		row = cur.fetchone()
		cur.close()
		return row
	except Exception as e:
		print(f"✗ DB Error: {e}")
		return None
	finally:
		if conn:
			conn.close()


@app.post("/auth/register", status_code=201)
def register(req: RegisterRequest):
	hashed = hash_password(req.password)
	try:
		row = insert_user(req.email, hashed)
		if not row:
			raise HTTPException(status_code=500, detail="✗ Failed to create user")
		return {"user_id": str(row[0]), "email": row[1]}
	except Exception as e:
		if isinstance(e, UniqueViolation) or (hasattr(e, 'pgcode') and getattr(e, 'pgcode', None) == '23505'):
			raise HTTPException(status_code=409, detail="✗ Email already registered")
		raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login")
def login(req: LoginRequest):
	row = fetch_user_by_email(req.email)
	if not row:
		raise HTTPException(status_code=401, detail="✗ Invalid credentials")
	user_id, email, password_hash = row[0], row[1], row[2]
	if not verify_password(req.password, password_hash):
		raise HTTPException(status_code=401, detail="✗ Invalid credentials")
	token = create_access_token(str(user_id), expires_hours=24)
	return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/health")
def health():
    return {"status": "healthy"}
