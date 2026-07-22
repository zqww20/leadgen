"""OpenSanctions — sanctions / PEP / watchlist screening.

Free to SELF-HOST (set OPENSANCTIONS_BASE_URL to your yente instance), or use
the hosted API with an API key (free keys available for non-commercial use;
commercial use is metered at ~EUR0.10/request). Set OPENSANCTIONS_API_KEY.
Docs: https://www.opensanctions.org/docs/api/
"""
from __future__ import annotations

from .base import Connector
from ..config import HTTP_TIMEOUT, get
from ..models import Finding, Subject

HOSTED = "https://api.opensanctions.org"


class OpenSanctions(Connector):
    name = "opensanctions"
    label = "OpenSanctions (sanctions / PEP)"
    category = "sanctions"
    free = False
    note = "Sanctions, PEPs and watchlists. Self-host for free, or use a hosted API key."

    def search(self, subject: Subject) -> list[Finding]:
        base = get("OPENSANCTIONS_BASE_URL") or HOSTED
        key = get("OPENSANCTIONS_API_KEY")
        s = self._session()
        if key:
            s.headers["Authorization"] = f"ApiKey {key}"

        body = {
            "queries": {
                "q1": {
                    "schema": "Person",
                    "properties": {"name": [subject.as_query()]},
                }
            }
        }
        r = s.post(f"{base}/match/default", json=body, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
        results = (payload.get("responses", {})
                          .get("q1", {})
                          .get("results", []))

        findings: list[Finding] = []
        for hit in results[:15]:
            props = hit.get("properties", {})
            datasets = hit.get("datasets", [])
            topics = props.get("topics", [])
            findings.append(Finding(
                source=self.name,
                category=self.category,
                title=hit.get("caption", subject.name),
                summary=f"Match score {hit.get('score', 0):.2f} on: {', '.join(datasets[:5]) or 'n/a'}."
                        f" Topics: {', '.join(topics) or 'n/a'}.",
                url=f"https://www.opensanctions.org/entities/{hit.get('id', '')}/",
                confidence="possible",
                data={
                    "score": hit.get("score"),
                    "schema": hit.get("schema"),
                    "datasets": datasets,
                    "topics": topics,
                    "countries": props.get("country", []),
                },
            ))
        return findings
