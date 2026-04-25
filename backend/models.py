"""
EmuFlow — SQLAlchemy 2.0 ORM models.

Three tables back the device telemetry layer:

- ``devices``             — one row per physical Android device. Identified
  by an opaque ``hardware_fingerprint`` (SHA-256 of stable hardware bits).
- ``device_events``       — append-only event log (heartbeat, install_*,
  launch, error, …). Carries an arbitrary JSONB payload.
- ``installed_emulators`` — current emulator inventory per device. The
  ``(device_id, package_name)`` pair is unique; new heartbeats upsert.

All timestamps are timezone-aware UTC. Primary keys are UUIDs (stored as
36-char strings for cross-DB portability — Postgres and SQLite alike).
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, TypeDecorator

from database import Base


class JSONType(TypeDecorator):
    """Use JSONB on Postgres, generic JSON elsewhere (SQLite tests)."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class EventType(str, enum.Enum):
    """Allowed values for ``DeviceEvent.event_type``."""

    install_started = "install_started"
    install_done = "install_done"
    install_failed = "install_failed"
    launch = "launch"
    error = "error"
    heartbeat = "heartbeat"


class Device(Base):
    """A registered Android device."""

    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    hardware_fingerprint: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    chipset: Mapped[str] = mapped_column(String(255), nullable=False)
    android_api: Mapped[int] = mapped_column(Integer, nullable=False)
    ram_gb: Mapped[float] = mapped_column(Float, nullable=False)
    shizuku_available: Mapped[bool] = mapped_column(default=False, nullable=False)
    agent_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    events: Mapped[list["DeviceEvent"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="DeviceEvent.created_at.desc()",
    )
    installed_emulators: Mapped[list["InstalledEmulator"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )


class DeviceEvent(Base):
    """An append-only event emitted by an agent."""

    __tablename__ = "device_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    device_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(
        SAEnum(EventType, name="device_event_type"), nullable=False, index=True
    )
    payload: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    device: Mapped[Device] = relationship(back_populates="events")


class InstalledEmulator(Base):
    """An emulator package present on a device at last heartbeat."""

    __tablename__ = "installed_emulators"
    __table_args__ = (
        UniqueConstraint("device_id", "package_name", name="uq_device_package"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    device_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    install_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    device: Mapped[Device] = relationship(back_populates="installed_emulators")
