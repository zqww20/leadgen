"""People Data Labs — person enrichment (PAID, ~$0.20-0.28/match).

Enrich a name (+ locality/company/email) into employment, emails, phones,
profiles. Needs PDL_API_KEY. Docs: https://docs.peopledatalabs.com/
"""
from __future__ import annotations

from .base import Connector
from ..config import HTTP_TIMEOUT, get
from ..models import Finding, Subject

BASE = "https://api.peopledatalabs.com/v5/person/enrich"


class PeopleDataLabs(Connector):
    name = "peopledatalabs"
    label = "People Data Labs (identity enrichment)"
    category = "identity"
    free = False
    note = "Paid. ~$0.20-0.28 per matched person. Set PDL_API_KEY."

    def search(self, subject: Subject) -> list[Finding]:
        s = self._session()
        s.headers["X-Api-Key"] = get("PDL_API_KEY")
        params: dict[str, str] = {"name": subject.as_query(), "min_likelihood": "6"}
        if subject.location:
            params["location"] = subject.location
        if subject.employer:
            params["company"] = subject.employer
        if subject.emails:
            params["email"] = subject.emails[0]
        r = s.get(BASE, params=params, timeout=HTTP_TIMEOUT)
        if r.status_code == 404:
            return []  # no match is a normal outcome
        r.raise_for_status()
        payload = r.json()
        data = payload.get("data") or {}
        if not data:
            return []
        exp = data.get("experience") or []
        job = exp[0].get("company", {}).get("name") if exp else data.get("job_company_name")
        return [Finding(
            source=self.name, category=self.category,
            title=data.get("full_name", subject.name),
            summary=f"Match (likelihood {payload.get('likelihood')}). "
                    f"Current: {data.get('job_title') or '?'} @ {job or '?'}.",
            url=(data.get("linkedin_url") and f"https://{data['linkedin_url']}") or "",
            confidence="possible",
            data={
                "emails": [e.get("address") for e in (data.get("emails") or [])],
                "phones": data.get("phone_numbers"),
                "location": data.get("location_name"),
                "profiles": [p.get("url") for p in (data.get("profiles") or [])],
                "job_history": [f"{e.get('title', {}).get('name')} @ {e.get('company', {}).get('name')}" for e in exp[:5]],
            },
        )]
