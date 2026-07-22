"""Certn — CONSENT-BASED Canadian criminal / background check (PAID).

⚠ This is the legal path for criminal records in Canada: it requires the
subject's informed consent (CPIC checks are consent + identity gated). This
connector will NOT run unless you pass --consent AND supply the subject's
email, which Certn uses to collect consent directly from the applicant.

Needs CERTN_API_KEY. Docs: https://docs.certn.co/
"""
from __future__ import annotations

from .base import Connector
from ..config import HTTP_TIMEOUT, get
from ..models import Finding, Subject

BASE = "https://api.certn.co/hr/v1/applications/"


class Certn(Connector):
    name = "certn"
    label = "Certn (consent-based criminal check)"
    category = "litigation"
    free = False
    note = "Paid + CONSENT REQUIRED. Initiates a CPIC criminal check via the subject's email."

    def search(self, subject: Subject) -> list[Finding]:
        # Hard guards: consent flag + subject email are mandatory.
        if not subject.notes.startswith("CONSENT:"):
            return [Finding(
                source=self.name, category=self.category,
                title="Criminal check NOT run — consent required",
                summary="Certn is skipped unless you pass --consent (records the subject's "
                        "informed consent). Canadian criminal records cannot be pulled without it.",
                confidence="unverified", data={"skipped": "no_consent"},
            )]
        if not subject.emails:
            return [Finding(
                source=self.name, category=self.category,
                title="Criminal check NOT run — no subject email",
                summary="Certn collects consent from the applicant by email; supply --email.",
                confidence="unverified", data={"skipped": "no_email"},
            )]

        s = self._session()
        s.headers["Authorization"] = f"Token {get('CERTN_API_KEY')}"
        body = {
            "email": subject.emails[0],
            "request_criminal_record_check": True,
            # Certn emails the applicant to collect consent + identity itself.
        }
        r = s.post(BASE, json=body, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        app = r.json()
        return [Finding(
            source=self.name, category=self.category,
            title=f"Certn criminal check initiated ({app.get('id', '?')})",
            summary=f"Status: {app.get('status', 'pending')}. Applicant emailed for consent; "
                    "results return once they complete identity verification.",
            url=app.get("report_url", ""),
            confidence="confirmed",
            data={"application_id": app.get("id"), "status": app.get("status")},
        )]
