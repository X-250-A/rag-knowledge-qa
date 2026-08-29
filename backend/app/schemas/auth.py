from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(max_length=10, min_length=1)
    password: str = Field(max_length=128, min_length=6)


class RegisterResponse(BaseModel):
    username: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    token: str
    token_type: str
