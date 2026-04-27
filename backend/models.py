"""
EmuFlow — SQLAlchemy 2.0 ORM models.

Tables:

- ``devices``             — one row per physical Android device. Identified
  by an opaque ``hardware_fingerprint`` (SHA-256 of stable hardware bits).
- ``device_events``       — append-only event log (heartbeat, install_*,
  launch, error, …). Carries an arbitrary JSONB payload.
- ``installed_emulators`` — current emulator inventory per device. The
  ``(device_id, package_name)`` pair is unique; new heartbeats upsert.
- ``crash_events``        — crash telemetry from the on-device agent.
  No ROM filenames or hashes; game_id is official product code only (DSA-safe).

All timestamps are timezone-aware UTC. Primary keys are UUIDs (stored as
36-char strings for cross-DB portability — Postgres and SQLite alike).
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
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
    shizuku_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    agent_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # --- Phase 1 OS / hardware fields ---

    manufacturer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    android_release: Mapped[str | None] = mapped_column(String(32), nullable=True)

    soc_vendor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    soc_chip: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gpu_family: Mapped[str | None] = mapped_column(String(128), nullable=True)

    page_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ram_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)

    shizuku_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_rooted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    has_analog_sticks: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # dual_stick / no_stick / single_stick
    controller_layout: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # List of vendor shell package names (no ROM hashes/filenames — DSA art. 6 safe)
    vendor_shell_packages: Mapped[list | None] = mapped_column(JSONType, nullable=True)

    thermal_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    battery_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)

    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Admin-only: never surfaced in non-admin responses
    last_known_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Save-events aggregates (last 24 h window, from heartbeat payload)
    save_events_24h: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

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
    crash_events: Mapped[list["CrashEvent"]] = relationship(
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


class CrashEvent(Base):
    """A crash reported by the on-device agent.

    No ROM filenames, no ROM hashes. ``game_id`` is an official product code
    (e.g. SLUS-00123) — not a file path. DSA art. 6 compliant.
    """

    __tablename__ = "crash_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    device_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Emulator context
    emulator_package: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emulator_version_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    emulator_version_code: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Game context — official product code ONLY (no file paths/hashes)
    game_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duration_played_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Crash classification
    crash_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    crash_signal: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Memory snapshot at crash time
    rss_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pss_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Tombstone — hash only, no content
    stacktrace_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Max 4096 chars, excerpt only
    tombstone_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Environmental context at crash time
    thermal_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    battery_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery_temperature_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    free_ram_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    device: Mapped[Device] = relationship(back_populates="crash_events")
