from pathlib import Path

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings


DATABASE_PATH = Path(settings.database_path).expanduser()

if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = (
        Path(__file__).resolve().parent / DATABASE_PATH
    )

DATABASE_PATH = DATABASE_PATH.resolve()

if not DATABASE_PATH.parent.is_dir():
    raise RuntimeError(
        "The directory specified by DATABASE_PATH must exist"
    )

DATABASE_URL = URL.create(
    "sqlite",
    database=str(DATABASE_PATH),
)

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": settings.sqlite_timeout_seconds,
    },
)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as session:
        yield session