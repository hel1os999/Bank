import logging
from typing import Callable, Awaitable

import time, uuid

from fastapi import FastAPI, Request, Response

import log_settings

log = logging.getLogger("APP_LOGGER")

def middlewares(app: FastAPI) -> None:


    @app.middleware("http")
    async def log_new_request(
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]]
    ):

        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception:
            log.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            raise

        duration = (time.perf_counter() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id

        response.headers["Cache-Control"] = "no-store"

        log.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "status_code": response.status_code,
                "cache_status": response.headers.get("x-fastapi-cache"),
                "duration_ms": round(duration, 2),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        return response