
import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "NOT_FOUND"
                if exc.status_code == 404
                else "HTTP_ERROR",
                "message": str(exc.detail),
            }
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": [
                    {
                        "loc": list(error["loc"]),
                        "message": error["msg"],
                        "type": error["type"],
                    }
                    for error in exc.errors()
                ],
            }
        },
    )


async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.error(
        "Unhandled exception at %s %s",
        request.method,
        request.url.path,
        exc_info=(
            type(exc),
            exc,
            exc.__traceback__,
        ),
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )
