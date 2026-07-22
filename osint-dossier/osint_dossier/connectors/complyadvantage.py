"""ComplyAdvantage — PEP / sanctions / adverse-media screening (PAID).

NLP-filtered adverse media plus PEP & watchlists. Needs COMPLYADVANTAGE_API_KEY.
Docs: https://docs.complyadvantage.com/
"""
from __future__ import annotations

from .base import Connector
from ..config import HTTP_TIMEOUT, get
from ..models import Finding, Subject

BASE = "https://api.complyadvantage.com/searches"


class ComplyAdvantage(Connector):
    name = "complyadvantage"
    label = "ComplyAdvantage (PEP / adverse media)"
    category = "sanctions"
    free = False
    note = "Paid (from ~$99/mo). PEP, sanctions & NLP adverse media. Set COMPLYADVANTAGE_API_KEY."

    def search(self, subject: Subject) -> list[Finding]:
        s = self._session()
        body = {
            "search_term": subject.as_query(),
            "fuzziness": 0.6,
            "filters": {"types": ["sanction", "warning", "pep", "adverse-media"]},
            "share_url": 1,
        }
        r = s.post(f"{BASE}?api_key={get('COMPLYADVANTAGE_API_KEY')}",
                   json=body, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        content = r.json().get("content", {}).get("data", {})
        hits = content.get("hits", [])
        findings: list[Finding] = []
        for h in hits[:20]:
            doc = h.get("doc", {})
            findings.append(Finding(
                source=self.name, category=self.category,
                title=doc.get("name", subject.name),
                summary=f"Match score {h.get('score')}. Types: {', '.join(doc.get('types', [])) or 'n/a'}.",
                url=content.get("share_url", ""),
                confidence="possible",
                data={
                    "types": doc.get("types"),
                    "score": h.get("score"),
                    "countries": doc.get("countries"),
                    "match_types": h.get("match_types"),
                },
            ))
        return findings
