import os
import secrets
from pathlib import Path
from typing import Annotated
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from config import settings

from models import RefreshSession
from security import create_refresh_token
from sqlalchemy import update
from schemas import RefreshRequest
from security import hash_refresh_token

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import (
    APIKeyHeader,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from models import Student, User
from schemas import (
    StudentCreate,
    StudentResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    get_jwt_secret,
    hash_password,
    verify_password,
)


API_KEY = settings.api_key.get_secret_value()
app = FastAPI(
    title="Student Scores API",
    description="Analyse student scores with API-key and JWT authentication.",
    version="0.3.0",
)

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)

bearer_scheme = HTTPBearer(auto_error=False)


def verify_api_key(
    supplied_key: str | None = Security(api_key_header),
):
    if supplied_key is None or not secrets.compare_digest(
        supplied_key.encode("utf-8"),
        API_KEY.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
):
    auth_error = HTTPException(
        status_code=401,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise auth_error

    try:
        payload = jwt.decode(
            credentials.credentials,
            get_jwt_secret(),
            algorithms=["HS256"],
            options={"require": ["sub", "iat", "exp"]},
        )

        user_id = int(payload["sub"])

        if user_id <= 0:
            raise ValueError("Invalid user ID")

    except (InvalidTokenError, ValueError, TypeError):
        raise auth_error

    user = db.get(User, user_id)

    if user is None:
        raise auth_error

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return current_user

def revoke_refresh_family(db: Session, family_id: str):
    db.execute(
        update(RefreshSession)
        .where(RefreshSession.family_id == family_id)
        .values(revoked=True)
        .execution_options(synchronize_session=False)
    )




class StudentRequest(BaseModel):
    scores: dict[
        str,
        Annotated[float, Field(ge=0, le=100)],
    ] = Field(min_length=1)

    pass_mark: float = Field(default=50, ge=0, le=100)


@app.get("/")
def home():
    return {"message": "Student Scores API is running"}


@app.post(
    "/passing-students",
    dependencies=[Depends(verify_api_key)],
    summary="Analyse student results",
)
def passing_students(request: StudentRequest):
    """Classify scores and return a results summary."""
    passed = {}
    failed = {}

    for name, score in request.scores.items():
        if score >= request.pass_mark:
            passed[name] = score
        else:
            failed[name] = score

    total_students = len(request.scores)
    average_score = sum(request.scores.values()) / total_students

    return {
        "pass_mark": request.pass_mark,
        "total_students": total_students,
        "passed_count": len(passed),
        "failed_count": len(failed),
        "average_score": round(average_score, 2),
        "passed": passed,
        "failed": failed,
    }


@app.post(
    "/students",
    response_model=StudentResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_student(
    request: StudentCreate,
    db: Session = Depends(get_db),
):
    student = Student(
        name=request.name,
        score=request.score,
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return student


@app.get(
    "/students/{student_id}",
    response_model=StudentResponse,
   dependencies=[Depends(require_admin)],
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    return student


@app.get(
    "/students",
    response_model=list[StudentResponse],
    dependencies=[Depends(require_admin)],
)
def list_students(
    db: Session = Depends(get_db),
):
    statement = select(Student).order_by(Student.id)
    students = db.scalars(statement).all()

    return students


@app.put(
    "/students/{student_id}",
    response_model=StudentResponse,
    dependencies=[Depends(require_admin)],
)
def update_student(
    student_id: int,
    request: StudentCreate,
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    student.name = request.name
    student.score = request.score

    db.commit()
    db.refresh(student)

    return student


@app.delete(
    "/students/{student_id}",
    response_model=StudentResponse,
   dependencies=[Depends(require_admin)],
)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    deleted_student = StudentResponse.model_validate(student)

    db.delete(student)
    db.commit()

    return deleted_student


@app.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
)
def register_user(
    request: UserCreate,
    db: Session = Depends(get_db),
):
    user = User(
        username=request.username,
        password_hash=hash_password(request.password),
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to register: username may already exist",
        )

    db.refresh(user)

    return user


@app.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: UserLogin,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.username == request.username)
    )

    stored_hash = (
        user.password_hash
        if user is not None
        else DUMMY_PASSWORD_HASH
    )

    password_matches = verify_password(
        request.password,
        stored_hash,
    )

    if user is None or not password_matches:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(user.id)
    refresh_token, token_hash = create_refresh_token()

    expires_at = int(
        (
            datetime.now(timezone.utc)
            + + timedelta(days=settings.refresh_token_days)
        ).timestamp()
    )

    refresh_session = RefreshSession(
        user_id=user.id,
        token_hash=token_hash,
        family_id=str(uuid4()),
        expires_at=expires_at,
        revoked=False,
    )

    db.add(refresh_session)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
@app.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@app.get("/admin/check")
def check_admin_access(
    current_user: User = Depends(require_admin),
):
    return {
        "message": "Admin access granted",
        "username": current_user.username,
    }
@app.post("/refresh", response_model=TokenResponse)
def refresh_tokens(
    request: RefreshRequest,
    db: Session = Depends(get_db),
):
    auth_error = HTTPException(
        status_code=401,
        detail="Invalid or expired refresh token",
    )

    token_hash = hash_refresh_token(request.refresh_token)

    session_record = db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == token_hash
        )
    )

    if session_record is None:
        raise auth_error

    now = int(datetime.now(timezone.utc).timestamp())

    if session_record.expires_at <= now:
        raise auth_error

    if session_record.revoked:
        revoke_refresh_family(db, session_record.family_id)
        db.commit()
        raise auth_error

    user = db.get(User, session_record.user_id)

    if user is None:
        raise auth_error

    access_token = create_access_token(user.id)
    new_token, new_hash = create_refresh_token()

    # Consume the old token only if it is still active.
    result = db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.id == session_record.id,
            RefreshSession.revoked.is_(False),
            RefreshSession.expires_at > now,
        )
        .values(revoked=True)
        .execution_options(synchronize_session=False)
    )

    if result.rowcount != 1:
        revoke_refresh_family(db, session_record.family_id)
        db.commit()
        raise auth_error

    replacement = RefreshSession(
        user_id=user.id,
        token_hash=new_hash,
        family_id=session_record.family_id,
        expires_at=session_record.expires_at,
        revoked=False,
    )

    db.add(replacement)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_token,
        "token_type": "bearer",
    }
@app.post("/logout")
def logout(
    request: RefreshRequest,
    db: Session = Depends(get_db),
):
    token_hash = hash_refresh_token(request.refresh_token)

    session_record = db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == token_hash
        )
    )

    if session_record is not None:
        revoke_refresh_family(
            db,
            session_record.family_id,
        )
        db.commit()

    return {"message": "Logged out"}
