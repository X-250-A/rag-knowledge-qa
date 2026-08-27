import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from backend.app.config import settings


# 哈希加密
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# 校验密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


# 生成token
def create_access_token(payload : dict):
    payload = payload.copy() # 复制原始数据
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES) # 计算过期时间
    # 插入token业务字段
    payload.update({
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "jti": str(uuid.uuid4())
    })
    # 生成token
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHMS[0])
    return token

# 解码token
def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, settings.ALGORITHMS[0])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("token已过期")
    except jwt.InvalidTokenError:
        raise ValueError("无效的token")


