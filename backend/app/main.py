from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    request_validation_error_handler,
)
from fastapi.exceptions import RequestValidationError

from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title=get_settings().app_name)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def root_health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
