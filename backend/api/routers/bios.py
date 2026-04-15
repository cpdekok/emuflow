"""
EmuFlow API — BIOS Router
Validates uploaded BIOS file hashes against a known-good database.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from core.bios.checker import BIOSChecker, BIOSCheckResult

router = APIRouter()
_checker = BIOSChecker()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class BIOSEntry(BaseModel):
    """A single BIOS file submission for validation."""

    filename: str
    md5: str


class BIOSValidateRequest(BaseModel):
    """List of BIOS files to validate."""

    files: list[BIOSEntry]


class BIOSFileResult(BaseModel):
    """Validation result for one BIOS file."""

    filename: str
    md5: str
    status: str          # "passed" | "failed" | "unknown"
    system: str | None = None
    notes: str | None = None


class BIOSValidateResponse(BaseModel):
    """Aggregated validation results."""

    results: list[BIOSFileResult]
    passed: int
    failed: int
    unknown: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/validate", response_model=BIOSValidateResponse)
async def validate_bios(payload: BIOSValidateRequest) -> BIOSValidateResponse:
    """
    Validate a list of BIOS files by comparing their MD5 hashes against the
    internal known-good database.

    Each entry returns one of three statuses:
    - **passed** — hash matches a known-good entry
    - **failed**  — filename is known but hash does not match (corrupted / wrong region)
    - **unknown** — filename is not in the database at all
    """
    results: list[BIOSFileResult] = []
    counts = {"passed": 0, "failed": 0, "unknown": 0}

    for entry in payload.files:
        result_enum = _checker.check_file(entry.filename, entry.md5)
        status = result_enum.value  # "passed" / "failed" / "unknown"
        counts[status] += 1

        # Attach extra metadata when available
        db_entry = _checker.BIOS_HASHES.get(entry.filename.lower())
        results.append(
            BIOSFileResult(
                filename=entry.filename,
                md5=entry.md5,
                status=status,
                system=db_entry.system if db_entry else None,
                notes=db_entry.notes if db_entry else None,
            )
        )

    return BIOSValidateResponse(
        results=results,
        passed=counts["passed"],
        failed=counts["failed"],
        unknown=counts["unknown"],
    )


@router.get("/database", summary="Get full BIOS hash database")
async def get_bios_database() -> dict:
    """
    Return the complete internal BIOS hash database with all known-good MD5
    hashes, system associations, and notes.
    """
    db = {
        filename: {
            "system": entry.system,
            "md5": entry.md5,
            "required": entry.required,
            "notes": entry.notes,
        }
        for filename, entry in _checker.BIOS_HASHES.items()
    }
    return {"database": db, "count": len(db)}
