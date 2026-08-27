from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.crud import (
    get_current_user,
    verify_user,
    find_user_by_username,
    create_user,
)
from backend.app.db import get_db
from backend.app.models import User
from backend.app.schemas import (
    RegisterResponse,
    LoginResponse,
    RegisterRequest,
    LoginRequest,
)
from backend.app.utils import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])



@router.post("/register")
async def register(user: RegisterRequest, db:AsyncSession = Depends(get_db)):
    existing = await find_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = await create_user(db, user)
    return RegisterResponse(username=new_user.username)


@router.post("/login")
async def login(user: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await verify_user(db, user.username, user.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token({"user_id": user.id})
    return LoginResponse(token=token, token_type="bearer")


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return current_user








