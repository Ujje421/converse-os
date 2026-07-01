"""Global error handler middleware — converts exceptions into standard ApiResponse."""

from __future__ import annotations

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Awaitable, Callable

from converse_shared.application.dto import ApiResponse, ErrorDetail
from converse_shared.domain.exceptions import (
    AuthorizationError,
    BusinessRuleViolation,
    ConcurrencyConflict,
    DomainException,
    EntityAlreadyExists,
    EntityNotFound,
    RateLimitExceeded,
    TenantAccessDenied,
    ValidationError,
)

logger = structlog.get_logger()


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catches exceptions and formats them into standardized JSON responses."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            return await call_next(request)
        except EntityNotFound as e:
            return self._handle_domain_error(e, 404)
        except EntityAlreadyExists as e:
            return self._handle_domain_error(e, 409)
        except (AuthorizationError, TenantAccessDenied) as e:
            return self._handle_domain_error(e, 403)
        except RateLimitExceeded as e:
            return self._handle_domain_error(e, 429, headers={"Retry-After": str(e.retry_after or 60)})
        except ValidationError as e:
            return self._handle_domain_error(e, 422)
        except ConcurrencyConflict as e:
            return self._handle_domain_error(e, 409)
        except BusinessRuleViolation as e:
            return self._handle_domain_error(e, 422)
        except DomainException as e:
            return self._handle_domain_error(e, 400)
        except Exception as e:
            # Unhandled exceptions
            logger.exception("unhandled_exception", error=str(e), path=request.url.path)
            return JSONResponse(
                status_code=500,
                content=ApiResponse.fail(
                    error_code="INTERNAL_SERVER_ERROR",
                    message="An unexpected error occurred",
                    status_code=500,
                ).model_dump(),
            )

    def _handle_domain_error(self, exc: DomainException, status_code: int, headers: dict[str, str] | None = None) -> JSONResponse:
        """Format a DomainException into a standard ApiResponse JSONResponse."""
        if status_code >= 500:
            logger.error("domain_error", error_code=exc.error_code, message=exc.message, details=exc.details)
        else:
            logger.info("domain_error", error_code=exc.error_code, message=exc.message, details=exc.details)
            
        return JSONResponse(
            status_code=status_code,
            headers=headers,
            content=ApiResponse.fail(
                error_code=exc.error_code,
                message=exc.message,
                status_code=status_code,
            ).model_dump(),
        )
