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