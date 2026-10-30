import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr


load_dotenv(Path(__file__).with_name(".env"))


class AppSettings(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        hide_input_in_errors=True,
    )

    api_key: SecretStr = Field(min_length=1)
    jwt_secret: SecretStr = Field(min_length=32)

    access_token_minutes: int = Field(gt=0, le=60)
    refresh_token_days: int = Field(gt=0, le=30)


settings = AppSettings(
    api_key=os.getenv("STUDENT_API_KEY", ""),
    jwt_secret=os.getenv("JWT_SECRET_KEY", ""),
    access_token_minutes=os.getenv("ACCESS_TOKEN_MINUTES", "30"),
    refresh_token_days=os.getenv("REFRESH_TOKEN_DAYS", "7"),
)