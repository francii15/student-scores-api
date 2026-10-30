from sqlalchemy import CheckConstraint, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from sqlalchemy import Boolean, ForeignKey, false


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

class User(Base):
   __tablename__="users"
   role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="user",
        server_default="user",
    )

   id:Mapped[int]=mapped_column(primary_key=True)
   username: Mapped[str]=mapped_column(
      String(50),
      unique=True,
      nullable=False,
    )
 
   password_hash:Mapped[str]=mapped_column(
       String,
      nullable=False,
)
class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    family_id: Mapped[str] = mapped_column(
        String(36),
        index=True,
        nullable=False,
    )

    expires_at: Mapped[int] = mapped_column(
        nullable=False,
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )