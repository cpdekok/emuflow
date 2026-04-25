# EmuFlow Backend

FastAPI service powering EmuFlow's Android emulation setup assistant.

- **Stack:** FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL (asyncpg) · Alembic · Redis · slowapi
- **Hosting:** Railway (`backend-production-05dd.up.railway.app`)
- **Frontend:** <https://emuflow.app>

---

## Quick start (local)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Either run against a local Postgres ...
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/emuflow"
# ... or rely on the SQLite fallback for a quick smoke test:
unset DATABASE_URL  # uses sqlite+aiosqlite:///./emuflow_dev.db

# Apply migrations
alembic upgrade head

# Start the API
uvicorn main:app --reload --port 8000
```

Visit <http://localhost:8000/docs> for the interactive Swagger UI.

---

## Database setup

The app uses **async SQLAlchemy 2.0** with `asyncpg`. The `DATABASE_URL`
env var is read at startup and rewritten transparently:

| Input prefix       | Effective driver         |
| ------------------ | ------------------------ |
| `postgres://…`     | `postgresql+asyncpg://…` |
| `postgresql://…`   | `postgresql+asyncpg://…` |
| `sqlite:///…`      | `sqlite+aiosqlite:///…`  |

### Migrations

Alembic is configured at `backend/alembic.ini` with environment
auto-loading in `alembic/env.py`. Common commands:

```bash
alembic upgrade head                   # apply all migrations
alembic downgrade -1                   # roll back one migration
alembic revision --autogenerate -m "…" # generate a new migration
alembic current                        # show current head
```

The Railway deploy invokes `alembic upgrade head` automatically as a
**release command** — see `railway.json`.

---

## Endpoint overview

### Telemetry (`/devices`)

| Method | Path                       | Auth        | Description                                   |
| ------ | -------------------------- | ----------- | --------------------------------------------- |
| `POST` | `/devices/heartbeat`       | none (60/m) | Upsert device + emulators, log heartbeat event |
| `POST` | `/devices/{id}/events`     | none        | Append an event to a device's log             |
| `GET`  | `/devices`                 | none        | List devices with `online` flag (<5min)       |
| `GET`  | `/devices/{id}`            | none        | Device detail + last 50 events + emulators    |
| `GET`  | `/devices/{id}/events`     | none        | Paginated events (`?limit=&offset=&type=`)    |
| `GET`  | `/devices/{id}/profile`    | none        | Performance tier + emulator recommendations   |
| `POST` | `/devices/register`        | none        | **Deprecated** — use `/heartbeat`             |

Other routers (`/profiles`, `/bios`, `/controls`, `/updates`, `/support`)
are unchanged.

### Heartbeat payload

```jsonc
{
  "hardware_fingerprint": "<sha256 of stable hw bits>",
  "device_name": "Pixel 7",
  "chipset": "Google Tensor G2",
  "android_api": 33,
  "ram_gb": 8.0,
  "shizuku_available": true,
  "agent_version": "0.2.0",
  "battery_pct": 87,
  "storage_free_gb": 64.5,
  "installed_emulators": [
    { "package_name": "org.dolphinemu.dolphinemu", "version": "5.0-21000" }
  ]
}
```

### Curl example

```bash
curl -X POST https://backend-production-05dd.up.railway.app/devices/heartbeat \
  -H "Content-Type: application/json" \
  -H "X-Agent-Version: 0.2.0" \
  -d '{
    "hardware_fingerprint": "fp-aaaaaaaaaaaaaaaaaaaaaaaa",
    "device_name": "Pixel 7",
    "chipset": "Google Tensor G2",
    "android_api": 33,
    "ram_gb": 8.0,
    "shizuku_available": true,
    "agent_version": "0.2.0",
    "installed_emulators": []
  }'
```

The response includes the assigned `device_id`:

```json
{
  "device_id": "0cf2…",
  "server_time": "2026-04-25T18:30:00+00:00",
  "online": true
}
```

---

## Security

- **CORS** (in `main.py`): allow-list is `https://emuflow.app`,
  `https://www.emuflow.app`, `http://localhost:3000`, `http://localhost:3001`.
  Wildcards are explicitly disabled.
- **Rate limit:** `/devices/heartbeat` is capped at **60/min/IP** via
  `slowapi`.
- **Agent version check:** the `X-Agent-Version` header (or the
  `agent_version` field in the body) is parsed; outdated agents trigger
  a server-side warning log entry.
- No PII is required at the heartbeat endpoint — `hardware_fingerprint`
  should be a hash of stable hardware bits computed by the agent.

---

## Tests

```bash
pip install aiosqlite          # already in requirements.txt
pytest backend/tests -v
```

Tests run **fully in-process** against an in-memory SQLite database via
`httpx.ASGITransport`. The 10 cases cover:

- heartbeat insert + upsert
- event log + filter + pagination
- online-flag computation
- installed-emulator inventory replacement
- rate-limit (60/min)
- CORS preflight (allow-list + deny)
- legacy `/devices/register` backwards-compat

---

## Project layout

```
backend/
├── alembic/                    # migrations
├── alembic.ini
├── api/
│   └── routers/
│       ├── devices.py          # telemetry endpoints (this PR)
│       ├── profiles.py
│       ├── bios.py
│       ├── controls.py
│       ├── updates.py
│       └── support.py
├── core/                       # hardware profiler, BIOS checker, scheduler
├── services/                   # AI support agent
├── tests/
│   ├── conftest.py             # SQLite in-memory client fixture
│   └── test_devices_telemetry.py
├── database.py                 # async engine + sessionmaker
├── models.py                   # ORM tables
├── main.py                     # FastAPI app
├── Dockerfile
├── railway.json                # build + release + start command
├── requirements.txt
└── pytest.ini
```
