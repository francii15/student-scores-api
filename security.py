from pwdlib import PasswordHash
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import secrets
from config import settings


import jwt
from dotenv import load_dotenv
load_dotenv(Path(__file__).with_name(".env"))
password_hasher = PasswordHash.recommended()

DUMMY_PASSWORD_HASH = password_hasher.hash(
    "Dummy-password-for-timing-only!"
)

def hash_password(password:str)->str:
   return password_hasher.hash(password)

def verify_password(
    password:str,
    stored_hash:str,
)->bool:
   return password_hasher.verify(password,stored_hash)
def get_jwt_secret() -> str:
    return settings.jwt_secret.get_secret_value()

def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
       "exp": now + timedelta(
    minutes=settings.access_token_minutes
),
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm="HS256",
    )
def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def create_refresh_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(48)
    token_hash = hash_refresh_token(token)

    return token, token_hash