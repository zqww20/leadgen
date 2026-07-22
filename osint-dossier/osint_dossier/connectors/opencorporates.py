"""OpenCorporates — officer search across 140+ jurisdictions (PAID).

Finds companies where the subject is a named officer/director, incl. Canadian
provinces. Needs OPENCORPORATES_API_TOKEN. Docs: https://api.opencorporates.com/
"""
from __future__ import annotations

from .base import Connector
from ..config import HTTP_TIMEOUT, get
from ..models import Finding, Subject

BASE = "https://api.opencorporates.com/v0.4/officers/search"


class OpenCorporates(Connector):
    name = "opencorporates"
    label = "OpenCorporates (officer search)"
    category = "corporate"
    free = False
    note = "Paid (from ~GBP2,250/yr). Officer/director search. Set OPENCORPORATES_API_TOKEN."

    def search(self, subject: Subject) -> list[Finding]:
        s = self._session()
        params = {
            "q": subject.as_query(),
            "api_token": get("OPENCORPORATES_API_TOKEN"),
            "order": "score",
        }
        # Narrow to Canada when we can.
        prov = subject.province.lower().strip()
        if prov:
            params["jurisdiction_code"] = f"ca_{prov}"
        r = s.get(BASE, params=params, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        officers = r.json().get("results", {}).get("officers", [])
        findings: list[Finding] = []
        for o in officers[:25]:
            off = o.get("officer", {})
            comp = off.get("company", {})
            findings.append(Finding(
                source=self.name, category=self.category,
                title=f"{off.get('name')} — {off.get('position') or 'officer'}",
                summary=f"{comp.get('name', '?')} ({comp.get('jurisdiction_code', '?')}), "
                        f"company #{comp.get('company_number', '?')}.",
                url=off.get("opencorporates_url", ""),
                confidence="possible",
                data={
                    "position": off.get("position"),
                    "company_name": comp.get("name"),
                    "company_number": comp.get("company_number"),
                    "jurisdiction": comp.get("jurisdiction_code"),
                    "inactive": comp.get("inactive"),
                },
            ))
        return findings
