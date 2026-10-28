from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Student
from schemas import StudentCreate, StudentResponse
import os
import secrets
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field


load_dotenv(Path(__file__).with_name(".env"))

API_KEY = os.getenv("STUDENT_API_KEY")

if not API_KEY:
    raise RuntimeError("Set STUDENT_API_KEY in your .env file")


app = FastAPI(
    title="Student Scores API",
    description="Analyse student scores with API-key authentication.",
    version="0.3.0"
)

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


def verify_api_key(
    supplied_key: str | None = Security(api_key_header)
):
    if supplied_key is None or not secrets.compare_digest(
        supplied_key.encode("utf-8"),
        API_KEY.encode("utf-8")
    ):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key"
        )


class StudentRequest(BaseModel):
    scores: dict[
        str,
        Annotated[float, Field(ge=0, le=100)]
    ] = Field(min_length=1)

    pass_mark: float = Field(default=50, ge=0, le=100)


@app.get("/")
def home():
    return {"message": "Student Scores API is running"}


@app.post(
    "/passing-students",
    dependencies=[Depends(verify_api_key)],
    summary="Analyse student results"
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
        "failed": failed
    }
@app.post(
    "/students",
    response_model=StudentResponse,
    status_code=201,
    dependencies=[Depends(verify_api_key)],
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
     dependencies=[Depends(verify_api_key)],
)
def get_student(
   student_id:int,
   db:Session=Depends(get_db),
):
   student=db.get(Student,student_id)

    

   if student is None:
      raise HTTPException(
         status_code = 404,
         detail = "Student not found",
)
   return student

@app.get(
  "/students",
  response_model=list[StudentResponse],
  dependencies=[Depends(verify_api_key)],
)
def list_students(
    db:Session = Depends(get_db),
):
    statement=select(Student).order_by(Student.id)
    students=db.scalars(statement).all()
    
    return students
@app.put("/students/{student_id}",
     response_model=StudentResponse,
     dependencies=[Depends(verify_api_key)],
)
def update_student(
    student_id:int,
    request:StudentCreate,
    db:Session=Depends(get_db),
):
   student=db.get(Student,student_id)
   
   if student is None:
      raise HTTPException(
      status_code=404,
      detail="Student not found",
)
   student.name=request.name
   student.score=request.score
    
   db.commit()
   db.refresh(student)
   
   return student
@app.delete(
   "/students/{student_id}",
    response_model=StudentResponse,
    dependencies=[Depends(verify_api_key)],
)
def delete_student(
    student_id:int,
    db:Session=Depends(get_db),
):
  student = db.get(Student,student_id)

  if student is None:
    raise HTTPException(
         status_code=404,
         detail="Student not found",
)
  deleted_student=StudentResponse.model_validate(student)
  db.delete(student)
  db.commit()
  
  return deleted_student