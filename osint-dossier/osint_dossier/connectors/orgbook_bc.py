"""OrgBook BC — free, keyless BC corporate registry.

Surfaces registered businesses (incl. sole proprietorships / DBAs that may
carry a person's name) and their registration IDs. Great free starting point
for the corporate-footprint section on any BC-linked subject.
API docs: https://orgbook.gov.bc.ca/api/
"""
from __future__ import annotations

from .base import Connector
from ..config import HTTP_TIMEOUT
from ..models import Finding, Subject

BASE = "https://orgbook.gov.bc.ca/api/v4"


class OrgBookBC(Connector):
    name = "orgbook_bc"
    label = "OrgBook BC (corporate registry)"
    category = "corporate"
    free = True
    note = "Free BC registry. Matches registered business names, including names of sole proprietors."

    def search(self, subject: Subject) -> list[Finding]:
        s = self._session()
        params = {"q": subject.as_query(), "inactive": "false"}
        r = s.get(f"{BASE}/search/topic", params=params, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
        results = payload.get("results", []) if isinstance(payload, dict) else []

        findings: list[Finding] = []
        for item in results[:20]:
            names = item.get("names") or []
            display = names[0].get("text") if names else item.get("source_id", "?")
            reg = item.get("topic_source_id") or item.get("source_id") or ""
            url = f"https://orgbook.gov.bc.ca/entity/{reg}" if reg else ""
            findings.append(Finding(
                source=self.name,
                category=self.category,
                title=str(display),
                summary=f"Registered entity in BC (reg #{reg}). Verify officer/owner link to subject.",
                url=url,
                confidence="possible",
                data={
                    "registration_id": reg,
                    "type": item.get("type"),
                    "all_names": [n.get("text") for n in names],
                },
            ))
        return findings
