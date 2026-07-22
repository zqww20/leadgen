"""GDELT DOC 2.0 — free, keyless global news / adverse-media search.

Searches worldwide news coverage mentioning the subject and flags articles
whose headline contains adverse-signal keywords (fraud, charged, lawsuit...).
API: https://api.gdeltproject.org/api/v2/doc/doc
"""
from __future__ import annotations

from .base import Connector
from ..config import HTTP_TIMEOUT
from ..models import Finding, Subject

BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

ADVERSE_TERMS = [
    "fraud", "charged", "arrest", "lawsuit", "sued", "convicted", "guilty",
    "investigation", "scandal", "misconduct", "sanction", "laundering",
    "bankruptcy", "insolvency", "fined", "penalty", "allegation", "probe",
]


class Gdelt(Connector):
    name = "gdelt"
    label = "GDELT (adverse media / news)"
    category = "adverse_media"
    free = True
    note = "Free global news index. Headlines are auto-flagged for adverse keywords."

    def search(self, subject: Subject) -> list[Finding]:
        s = self._session()
        query = f'"{subject.as_query()}"'
        if subject.location:
            query += f' "{subject.location.split(",")[0].strip()}"'
        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": "40",
            "sort": "datedesc",
            "format": "json",
        }
        r = s.get(BASE, params=params, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        # GDELT sometimes returns empty body or non-JSON on no results.
        try:
            payload = r.json()
        except ValueError:
            return []
        articles = payload.get("articles", []) if isinstance(payload, dict) else []

        findings: list[Finding] = []
        for a in articles[:40]:
            title = a.get("title", "") or ""
            low = title.lower()
            hits = [t for t in ADVERSE_TERMS if t in low]
            findings.append(Finding(
                source=self.name,
                category=self.category,
                title=title or a.get("url", "article"),
                summary=("⚠ Adverse signal: " + ", ".join(hits)) if hits else "News mention.",
                url=a.get("url", ""),
                confidence="possible" if hits else "unverified",
                data={
                    "domain": a.get("domain"),
                    "seendate": a.get("seendate"),
                    "language": a.get("language"),
                    "sourcecountry": a.get("sourcecountry"),
                    "adverse_terms": hits,
                },
            ))
        # Adverse-flagged first.
        findings.sort(key=lambda f: bool(f.data.get("adverse_terms")), reverse=True)
        return findings
