from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str

class RegisterResponse(BaseModel):
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    token_type: str





