from pydantic import BaseModel,ConfigDict,Field


class StudentCreate(BaseModel):
     model_config = ConfigDict(str_strip_whitespace=True)
     

     name: str = Field(min_length=1,max_length=100)
     score:float = Field(ge=0,le=100,allow_inf_nan=False)

class StudentResponse(BaseModel):
     model_config = ConfigDict(from_attributes = True)


     id: int
     name:str
     score:float
class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-z0-9_]+$",
    )
    password: str = Field(
        min_length=15,
        max_length=128,
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=512)