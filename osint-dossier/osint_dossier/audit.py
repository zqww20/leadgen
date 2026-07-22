"""Append-only audit log + lawful-basis enforcement.

Running investigations on people in Canada engages PIPEDA (and provincial
privacy law). This module refuses to run without a stated lawful basis and
records every run to an immutable JSONL log, so you can demonstrate why each
search was performed. This is a compliance guardrail, not decoration.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path

CASES_DIR = Path(__file__).resolve().parent.parent / "cases"
AUDIT_LOG = CASES_DIR / "audit.log"


class LawfulBasisError(ValueError):
    """Raised when an investigation is attempted with no stated lawful basis."""


def require_basis(basis: str) -> str:
    basis = (basis or "").strip()
    if len(basis) < 8:
        raise LawfulBasisError(
            "A lawful basis is required (min 8 chars). Under PIPEDA you must be "
            "able to justify collecting personal information. Example: "
            '--basis "corporate due diligence, engagement #1234, client consent on file".'
        )
    return basis


def _hash_name(name: str) -> str:
    return hashlib.sha256(name.strip().lower().encode()).hexdigest()[:16]


def record(*, case_id: str, operator: str, subject_name: str,
           lawful_basis: str, connectors: list[str]) -> None:
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "case_id": case_id,
        "operator": operator or "unknown",
        # Store a hash of the name, not the name itself, in the shared log.
        "subject_sha256_16": _hash_name(subject_name),
        "lawful_basis": lawful_basis,
        "connectors": connectors,
    }
    with AUDIT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
