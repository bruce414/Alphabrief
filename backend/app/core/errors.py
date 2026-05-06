from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Domain error that maps to API_SPEC §16."""

    def __init__(
        self,
        *,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def error_payload(
    *,
    error_code: str,
    message: str,
    details: Any = None,
    timestamp: datetime | None = None,
) -> dict[str, Any]:
    ts = timestamp or datetime.now(UTC)
    iso = ts.isoformat().replace("+00:00", "Z")
    return {
        "errorCode": error_code,
        "message": message,
        "details": details,
        "timestamp": iso,
    }


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        ),
    )
