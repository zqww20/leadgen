"""Pipl — investigative identity resolution (PAID, investigations-gated).

The investigator standard: cross-references deep/public web into a unified
identity from name/email/phone. Needs PIPL_API_KEY (billed per match).
Docs: https://docs.pipl.com/
"""
from __future__ import annotations

from .base import Connector
from ..config import HTTP_TIMEOUT, get
from ..models import Finding, Subject

BASE = "https://api.pipl.com/search/"


class Pipl(Connector):
    name = "pipl"
    label = "Pipl (identity resolution)"
    category = "identity"
    free = False
    note = "Paid, investigations-gated. ~$0.10+/matched query. Set PIPL_API_KEY."

    def search(self, subject: Subject) -> list[Finding]:
        s = self._session()
        params: dict[str, str] = {"key": get("PIPL_API_KEY"), "pretty": "false"}
        if subject.emails:
            params["email"] = subject.emails[0]
        elif subject.phones:
            params["phone"] = subject.phones[0]
        else:
            params["raw_name"] = subject.as_query()
            if subject.location:
                params["raw_address"] = subject.location
        r = s.get(BASE, params=params, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        payload = r.json()

        people = []
        if payload.get("person"):
            people.append((payload["person"], "confirmed"))
        for p in payload.get("possible_persons", [])[:5]:
            people.append((p, "possible"))

        findings: list[Finding] = []
        for person, conf in people:
            names = [n.get("display") for n in person.get("names", [])]
            emails = [e.get("address") for e in person.get("emails", [])]
            phones = [p.get("display") for p in person.get("phones", [])]
            addrs = [a.get("display") for a in person.get("addresses", [])]
            jobs = [j.get("display") for j in person.get("jobs", [])]
            findings.append(Finding(
                source=self.name, category=self.category,
                title=names[0] if names else subject.name,
                summary=f"Pipl {conf} identity. {len(emails)} email(s), {len(phones)} phone(s), "
                        f"{len(addrs)} address(es).",
                url=(person.get("@search_pointer") and BASE) or "",
                confidence=conf,
                data={"names": names, "emails": emails, "phones": phones,
                      "addresses": addrs, "jobs": jobs,
                      "usernames": [u.get("content") for u in person.get("usernames", [])]},
            ))
        return findings
