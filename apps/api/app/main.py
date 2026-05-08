import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

import sentry_sdk
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.middleware.auth import AuthMiddleware
from app.middleware.error_handler import (
    custom_http_exception_handler,
    global_exception_handler,
    validation_exception_handler,
)
from app.middleware.logging import StructuredLoggingMiddleware
from app.middleware.tenant_context import TenantContextMiddleware
from app.routers import health, tenants, threads, users, approvals, milos, programs, integrations, billing, webhooks

if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

app = FastAPI(
    title="Milo API",
    version="0.1.0",
    description="Milo Platform API",
    openapi_url="/openapi.json",
    docs_url="/docs",
)

# Middlewares (order matters: last added is outermost)
# 3. Tenant Context (innermost, needs auth)
app.add_middleware(TenantContextMiddleware)
# 2. Auth (extracts JWT)
app.add_middleware(AuthMiddleware)
# 1. Logging
app.add_middleware(StructuredLoggingMiddleware)

# CORS (Outermost, must intercept OPTIONS before Auth)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For PoC
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(StarletteHTTPException, custom_http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(tenants.router)
app.include_router(threads.router)
app.include_router(approvals.router)
app.include_router(milos.router)
app.include_router(programs.router)
app.include_router(integrations.router)
app.include_router(billing.router)
app.include_router(webhooks.router)
