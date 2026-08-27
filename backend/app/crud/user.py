from fastapi import Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_db
from backend.app.models import User
from backend.app.schemas import RegisterRequest
from backend.app.utils import verify_password, hash_password


# 通过id查找用户
async def find_user_by_id(db: AsyncSession, user_id : int):
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

# 通过用户名查找用户
async def find_user_by_username(db: AsyncSession, username : str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()

# 创建新用户
async def create_user(db: AsyncSession, user: RegisterRequest):
    hashed = hash_password(user.password)
    new_user = User(
        username=user.username,
        hashed_password=hashed
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# 校验用户
async def verify_user(db: AsyncSession, username : str, password : str):
    existing_user = await find_user_by_username(db, username)
    if not existing_user:
        return None
    if not verify_password(password, existing_user.hashed_password):
        return None
    return existing_user

# 获取当前用户信息
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.state.user_id
    user = await find_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user





