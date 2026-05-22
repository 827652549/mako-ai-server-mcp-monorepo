"""
Vision MCP Server 主入口
"""
import asyncio
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import get_settings
from app.core.exceptions import (
    MCPException,
    general_exception_handler,
    mcp_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging, get_logger
from app.core.security import verify_origin
from app.mcp_server.app import mcp
from app.mcp_server.transport import create_protected_mcp_app
from app.utils.http_client import http_client

configure_logging()
logger = get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("vision_mcp_starting", model=settings.VISION_MODEL)
    async with mcp.session_manager.run():
        await http_client.start()
        logger.info("vision_mcp_started")
        yield
        logger.info("vision_mcp_shutting_down")
        await asyncio.sleep(5)
        await http_client.stop()
    logger.info("vision_mcp_shutdown_complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],
)

app.add_exception_handler(MCPException, mcp_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    start = time.time()
    response = await call_next(request)
    latency_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency_ms=latency_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def origin_verification_middleware(request: Request, call_next):
    skip_paths = ["/", "/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
    if request.url.path in skip_paths or request.url.path.startswith("/mcp"):
        return await call_next(request)
    try:
        verify_origin(request)
    except Exception as e:
        logger.warning("origin_verification_failed", error=str(e))
        raise
    return await call_next(request)


if settings.PROMETHEUS_ENABLED:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    logger.info("prometheus_enabled", endpoint="/metrics")

protected_mcp_app = create_protected_mcp_app()
app.mount("/mcp", protected_mcp_app)
logger.info("mcp_mounted", path="/mcp")


@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME,
        "vision_model": settings.VISION_MODEL,
    }


@app.get("/")
async def root() -> dict:
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "mcp_endpoint": "/mcp",
        "vision_model": settings.VISION_MODEL,
        "tools": ["vision_describe", "vision_ocr", "vision_compare", "vision_ui_audit"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_config=None)
