from collections.abc import Callable
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DomainException(Exception):
    """Base class for all domain and business rule errors."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR", status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class EntityNotFoundException(DomainException):
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            message=f"{entity_name} with id '{entity_id}' not found",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class RuleViolationException(DomainException):
    def __init__(self, rule_message: str):
        super().__init__(
            message=rule_message,
            code="RULE_VIOLATION",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainException)
    async def domain_exception_handler(_: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "code": exc.code,
                "message": exc.message,
            },
        )
