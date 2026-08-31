import time

from fastapi import Request

from backend.app.logging_config import logger


async def timing_middleware(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000
        logger.info(
            f"request finished method={request.method} path={request.url.path} "
            f"status={getattr(response, 'status_code', 500)} "
            f"elapsed_ms={round(elapsed_ms, 1)}",
        )
    return response
