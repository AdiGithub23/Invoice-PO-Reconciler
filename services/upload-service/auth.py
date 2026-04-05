import os
from fastapi import HTTPException, Header, status
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")

def get_current_user(authorization: str = Header(...)) -> str:
    """Validates the Bearer token and returns the user_id (UUID)."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token header")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


