import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI,Depends,HTTPException,Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel,Field
from typing import Annotated

load_dotenv(Path(__file__).with_name(".env"))

API_KEY = os.getenv("STUDENT_API_KEY")

if not API_KEY:
      raise RuntimeError("Set STUDENT_API_KEY in your .env file")

app = FastAPI(
	title = "Student Scores API",
	description = "Analyze student scores through an API.",version = "0.1.0"
)

api_key_header = APIKeyHeader(
    name = "X-API-Key",
    auto_error=False
)

def verify_api_key(
   supplied_key:str| None = Security(api_key_header)
):
   if supplied_key is None or not secrets.compare_digest(
      supplied_key.encode("utf-8"),
      API_KEY.encode("utf-8")
):
      raise HTTPException(
           status_code=401,
           detail = "Missing or invalid APi key"
)


class StudentRequest(BaseModel):
	scores: dict[str,Annotated[float,Field(ge =0,le = 100)]]

@app.get("/")
def home():
    return {"message" : "Student scores API is running"}

@app.post("/passing students",dependencies=[Depends(verify_api_key)])
def passing_students(request:StudentRequest):
    passed = {
        name : score
        for name,score in request.scores.items()
        if score>=50

}
    return {"passed":passed}