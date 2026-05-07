from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocket


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


class WarningNotAcknowledgedError(AppError):
    error_code = "WARNING_NOT_ACKNOWLEDGED"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, *, estimated_pct: float, warning_level: str) -> None:
        super().__init__(
            error_code=self.error_code,
            message=(
                f"Estimated impact {estimated_pct:.1f}% (level={warning_level}); "
                "user must acknowledge before proceeding."
            ),
            status_code=self.status_code,
            details={
                "estimatedAllowanceImpactPercent": estimated_pct,
                "warningLevel": warning_level,
            },
        )


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


async def app_error_handler(_request: Request | WebSocket, exc: Exception) -> JSONResponse:
    if not isinstance(_request, Request):
        raise exc
    if not isinstance(exc, AppError):
        raise exc
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        ),
    )


async def request_validation_error_handler(
    _request: Request | WebSocket, exc: Exception
) -> JSONResponse:
    if not isinstance(_request, Request):
        raise exc
    if not isinstance(exc, RequestValidationError):
        raise exc
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_payload(
            error_code="INVALID_INPUT",
            message="Invalid input",
            details=exc.errors(),
        ),
    )
