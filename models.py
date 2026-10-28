from sqlalchemy import CheckConstraint, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    score: Mapped[float] = mapped_column(Float)

    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 100",
            name="valid_student_score",
        ),
    )