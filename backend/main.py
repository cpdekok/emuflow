"""
EmuFlow API - Main FastAPI Application
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import devices, profiles, bios, controls, updates, support

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("emuflow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — runs startup and shutdown logic."""
    logger.info("EmuFlow API starting up...")
    logger.info("Database connection established (in-memory store for MVP)")
    yield
    logger.info("EmuFlow API shutting down...")


app = FastAPI(
    title="EmuFlow API",
    version="0.1.0",
    description="Backend API for EmuFlow — the Android emulation setup assistant.",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow all origins in development
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Returns API health status."""
    return {"status": "ok", "version": app.version}
