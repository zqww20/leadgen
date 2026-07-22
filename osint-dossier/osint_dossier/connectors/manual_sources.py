"""Manual sources — deep-links to Canadian registries with no public API.

Many high-value Canadian sources (federal & provincial corporate registries,
court records, bankruptcy, case law) have no queryable API, or gate it behind
licences. This connector generates pre-filled search links so the investigator
can click straight through. No network calls, always available.
"""
from __future__ import annotations

import urllib.parse as up

from .base import Connector
from ..models import Finding, Subject


def _q(text: str) -> str:
    return up.quote_plus(text)


class ManualSources(Connector):
    name = "manual_sources"
    label = "Registry deep-links (manual)"
    category = "manual"
    free = True
    note = "Pre-filled search links for sources with no API. Open and review by hand."

    def search(self, subject: Subject) -> list[Finding]:
        name = subject.as_query()
        q = _q(name)
        quoted = _q(f'"{name}"')
        links: list[tuple[str, str, str]] = [
            ("Corporations Canada (federal registry)",
             "https://ised-isde.canada.ca/cc/lgcy/fdrlCrpSrch.html",
             "Search federal corporations; check director/officer name matches."),
            ("Ontario Business Registry",
             "https://www.ontario.ca/page/ontario-business-registry",
             "Ontario entity & officer search (per-search fees may apply)."),
            ("Québec — Registraire des entreprises (REQ)",
             "https://www.registreentreprises.gouv.qc.ca/en/consulter/rechercher/",
             "Free Québec entity search incl. directors/shareholders."),
            ("CanLII (case law & tribunals)",
             f"https://www.canlii.org/en/#search/text={quoted}",
             "Litigation / judgments / tribunal decisions naming the subject."),
            ("OSB — Bankruptcy & Insolvency search",
             "https://www.ic.gc.ca/app/scr/bsf-osb/ins/login.html",
             "Federal insolvency records (per-search fee ~$8)."),
            ("BC Court Services Online (CSO)",
             "https://justice.gov.bc.ca/cso/index.do",
             "BC civil & criminal case search (per-search fee)."),
            ("Google — adverse dork",
             f"https://www.google.com/search?q={quoted}+%28fraud+OR+lawsuit+OR+charged+OR+convicted+OR+bankruptcy%29",
             "Targeted negative-news search."),
            ("LinkedIn people search",
             f"https://www.linkedin.com/search/results/people/?keywords={q}",
             "Confirm employment / professional history."),
            ("Facebook people search",
             f"https://www.facebook.com/search/people/?q={q}",
             "Public profile / social footprint."),
            ("Canada411 — reverse name lookup",
             f"https://www.canada411.ca/search/?stype=si&what={q}",
             "Free Canadian phone / address directory."),
            ("Google — professional register / licence",
             f"https://www.google.com/search?q={quoted}+(license+OR+registration+OR+college+OR+association)",
             "Find a free public professional register to verify credentials."),
        ]
        findings = [
            Finding(
                source=self.name, category=self.category, title=title,
                summary=desc, url=url, confidence="unverified",
                data={"manual": True},
            )
            for title, url, desc in links
        ]
        return findings
