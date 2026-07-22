"""Core data models for the OSINT dossier tool."""
from __future__ import annotations

import datetime as _dt
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


# Finding categories -> how they group in the dossier report.
CATEGORIES = [
    "identity",       # confirmed identity, aliases, contact, addresses
    "corporate",      # companies the person is tied to
    "litigation",     # court records, judgments
    "sanctions",      # sanctions / PEP / watchlists
    "adverse_media",  # negative news
    "social",         # online / social footprint
    "manual",         # deep-links to registries with no API
]


@dataclass
class Subject:
    """The person being investigated. Only `name` is required."""
    name: str
    aliases: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    usernames: list[str] = field(default_factory=list)
    location: str = ""        # free text, e.g. "Vancouver, BC"
    province: str = ""        # e.g. "BC", "ON"
    employer: str = ""
    dob: str = ""             # optional, YYYY or YYYY-MM-DD
    notes: str = ""

    def as_query(self) -> str:
        return self.name.strip()


@dataclass
class Finding:
    """A single piece of information returned by a connector."""
    source: str                       # connector name, e.g. "orgbook_bc"
    category: str                      # one of CATEGORIES
    title: str
    summary: str = ""
    url: str = ""
    confidence: str = "unverified"     # unverified | possible | confirmed
    data: dict[str, Any] = field(default_factory=dict)
    retrieved_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Dossier:
    """The assembled result of a single investigation run."""
    subject: Subject
    lawful_basis: str
    operator: str
    case_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: str = field(default_factory=_now)
    findings: list[Finding] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    connectors_run: list[str] = field(default_factory=list)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def add_error(self, source: str, message: str) -> None:
        self.errors.append({"source": source, "message": message})

    def by_category(self) -> dict[str, list[Finding]]:
        grouped: dict[str, list[Finding]] = {c: [] for c in CATEGORIES}
        for f in self.findings:
            grouped.setdefault(f.category, []).append(f)
        return grouped

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "created_at": self.created_at,
            "operator": self.operator,
            "lawful_basis": self.lawful_basis,
            "subject": asdict(self.subject),
            "connectors_run": self.connectors_run,
            "findings": [f.to_dict() for f in self.findings],
            "errors": self.errors,
            "summary": {
                "total_findings": len(self.findings),
                "by_category": {k: len(v) for k, v in self.by_category().items()},
                "errors": len(self.errors),
            },
        }
