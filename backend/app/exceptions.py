import logging
from typing import cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail: str = "Internal Server Error"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail: str = "Forbidden"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail: str = "Not Found"


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail: str = "Bad Request"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    default_detail: str = "Conflict"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail: str = "Unauthorized"


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    app_error = cast(AppError, exc)
    return JSONResponse(
        status_code=app_error.status_code,
        content={"detail": app_error.detail},
    )


async def _unhandled_handler(request, exc) -> JSONResponse:
    logger.exception("Unhandled exception during %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, _unhandled_handler)
