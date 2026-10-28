from pwdlib import PasswordHash
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
    secret = os.getenv("JWT_SECRET_KEY")

    if not secret:
        raise RuntimeError(
            "Set JWT_SECRET_KEY in your .env file"
        )

    return secret


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=30),
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm="HS256",
    )