from fastapi import Request
from fastapi.responses import JSONResponse
from starlette import status

from backend.app.utils import decode_token

PUBLIC_PATHS = frozenset(
    {
        "/",
        "/api/auth/register",
        "/api/auth/login",
        "/api/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
)


# JWT鉴权逻辑
async def jwt_middleware(request: Request, call_next):
    # 0，白名单校验
    # 白名单路径直接放行
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    # 1，获取验证信息
    authorization_header = request.headers.get("Authorization")
    if authorization_header is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authorization header is missing"},
        )

    # 2，校验验证信息
    if not authorization_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "token is invalid"},
        )

    # 3，获取并校验token
    token = authorization_header.replace("Bearer ", "")
    try:
        payload = decode_token(token)
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "token is invalid"},
        )

    user_id = payload.get("user_id")
    jti = payload.get("jti")

    # 4，id非空校验
    if user_id is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "token is invalid"},
        )

    request.state.user_id = user_id
    request.state.jti = jti

    # 鉴权完毕，放行
    response = await call_next(request)
    return response
