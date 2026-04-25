"""
EmuFlow API - Main FastAPI Application.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.routers import bios, controls, devices, profiles, support, updates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("emuflow")


# ---------------------------------------------------------------------------
# CORS — allow only first-party origins
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS: list[str] = [
    "https://emuflow.app",
    "https://www.emuflow.app",
    "http://localhost:3000",
    "http://localhost:3001",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler — runs startup and shutdown logic."""
    logger.info("EmuFlow API starting up...")
    # Engine import is lazy to keep CLI tools (alembic) light.
    from database import DATABASE_URL

    redacted = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
    logger.info("Database target: %s", redacted)
    yield
    logger.info("EmuFlow API shutting down...")


app = FastAPI(
    title="EmuFlow API",
    version="0.2.0",
    description="Backend API for EmuFlow — the Android emulation setup assistant.",
    lifespan=lifespan,
)

# Attach the slowapi limiter from the devices router so the limit decorators
# share state app-wide.
app.state.limiter = devices.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(devices.router, prefix="/devices", tags=["Devices"])
app.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
app.include_router(bios.router, prefix="/bios", tags=["BIOS"])
app.include_router(controls.router, prefix="/controls", tags=["Controls"])
app.include_router(updates.router, prefix="/updates", tags=["Updates"])
app.include_router(support.router, prefix="/support", tags=["Support"])


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Returns API health status."""
    return {"status": "ok", "version": app.version}


# Legacy fallback so a stray uncaught error returns JSON, not HTML.
@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:  # pragma: no cover
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "internal_error"})
