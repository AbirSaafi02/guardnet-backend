from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional




class UserCreate(BaseModel):
    email :EmailStr
    nom :str
    password:str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    nom: str
    created_at: datetime

    class Config:

        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"




class PasswordChange(BaseModel):
    old_password: str
    new_password: str


