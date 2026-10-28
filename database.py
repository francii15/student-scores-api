from pathlib import Path
from sqlalchemy.orm import DeclarativeBase,sessionmaker
from sqlalchemy import URL, create_engine

DATABASE_PATH = Path(__file__).with_name("students.db")

DATABASE_URL = URL.create(
   "sqlite",
   database=str(DATABASE_PATH),
)

engine = create_engine(
   DATABASE_URL,
   connect_args={"check_same_thread":False},
)

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
   pass

def get_db():
    with SessionLocal() as session:
         yield session