import json
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("milo.api")
logger.setLevel(logging.INFO)

# Ensure no duplicate handlers if imported multiple times
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Safely extract context if auth middleware populated it
            tenant_id = getattr(request.state, "tenant_id", None)
            user_id = getattr(request.state, "user_id", None)

            log_entry = {
                "request_id": request_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "latency_ms": round(latency_ms, 2),
                "level": "INFO" if status_code < 400 else ("WARNING" if status_code < 500 else "ERROR"),
                "message": f"{request.method} {request.url.path} {status_code}",
            }

            if log_entry["level"] == "INFO":
                logger.info(json.dumps(log_entry))
            elif log_entry["level"] == "WARNING":
                logger.warning(json.dumps(log_entry))
            else:
                logger.error(json.dumps(log_entry))

        return response
