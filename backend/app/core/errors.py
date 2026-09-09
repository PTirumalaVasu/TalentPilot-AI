import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# The fixed top-level keys _error_body() always produces -- extra (below)
# must never collide with these, or it would silently overwrite part of the
# standard envelope in http_exception_handler's `{**_error_body(...), **extra}`
# merge.
_RESERVED_ENVELOPE_KEYS = frozenset({"status", "code", "message", "timestamp"})


class AppException(StarletteHTTPException):
    """HTTPException carrying a caller-supplied error code for the response body's
    `code` field. Plain HTTPException instances (no error_code attribute) still
    fall back to the generic HTTP_ERROR code, via http_exception_handler below.

    `extra` merges additional top-level fields into the response body, on top
    of the standard status/code/message/timestamp envelope -- e.g. Story
    6.2's 409 conflict response, which must also carry the existing Skill's
    id/name for the caller. Optional and empty by default so every existing
    call site is unaffected."""

    def __init__(self, status_code: int, error_code: str, message: str, extra: dict | None = None) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        extra = extra or {}
        collisions = extra.keys() & _RESERVED_ENVELOPE_KEYS
        if collisions:
            raise ValueError(f"AppException extra keys collide with the reserved envelope: {sorted(collisions)}")
        self.extra = extra


def _error_body(code: str, message: str) -> dict:
    return {
        "status": "error",
        "code": code,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body("VALIDATION_ERROR", "The request body failed validation"),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = getattr(exc, "error_code", "HTTP_ERROR")
        extra = getattr(exc, "extra", {})
        return JSONResponse(
            status_code=exc.status_code,
            content={**_error_body(code, str(exc.detail)), **extra},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("INTERNAL_SERVER_ERROR", "An unexpected error occurred"),
        )
