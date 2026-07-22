"""Free watchlist / sanctions / PEP screening — the $0 equivalent of Certn's
"Public Records Check / SoftCheck" ($9.99).

Fetches official, free, public sanctions lists at runtime and fuzzy-matches the
subject's name locally. No API key, no third party. Sources are configurable;
two reliable feeds ship on by default (US OFAC SDN + UN Consolidated). Add
Canada (SEMA), UK (OFSI) or EU via OSINT_WATCHLIST_FEEDS.

Matching uses stdlib only (difflib + accent folding) so there are no extra deps.
"""
from __future__ import annotations

import csv
import io
import time
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from .base import Connector
from ..config import HTTP_TIMEOUT, get
from ..models import Finding, Subject

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "cases" / ".cache"
CACHE_TTL = 24 * 3600  # refresh feeds daily
DEFAULT_THRESHOLD = 0.86


@dataclass
class Entry:
    name: str
    source: str
    detail: str = ""
    url: str = ""


# ---------------------------------------------------------------- name matching
def normalize(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = name.lower()
    return " ".join("".join(ch for ch in name if ch.isalnum() or ch.isspace()).split())


def _token_sort(name: str) -> str:
    return " ".join(sorted(normalize(name).split()))


def score(query: str, candidate: str) -> float:
    q, c = _token_sort(query), _token_sort(candidate)
    if not q or not c:
        return 0.0
    if q == c:
        return 1.0
    # Reward full-token containment (e.g. query is a subset of a longer listed name).
    qset, cset = set(q.split()), set(c.split())
    if qset and qset <= cset:
        return max(0.9, SequenceMatcher(None, q, c).ratio())
    return SequenceMatcher(None, q, c).ratio()


# ---------------------------------------------------------------- feed parsers
def parse_ofac_sdn(raw: bytes) -> list[Entry]:
    """US OFAC SDN list — headerless positional CSV."""
    entries: list[Entry] = []
    reader = csv.reader(io.StringIO(raw.decode("latin-1", errors="replace")))
    for row in reader:
        if len(row) < 4:
            continue
        name, sdn_type, program = row[1].strip(), row[2].strip(), row[3].strip()
        if not name or name == "-0-":
            continue
        entries.append(Entry(
            name=name, source="OFAC SDN (US Treasury)",
            detail=f"{sdn_type or 'entity'} · {program or 'sanctioned'}",
            url="https://sanctionssearch.ofac.treas.gov/",
        ))
    return entries


def parse_un_consolidated(raw: bytes) -> list[Entry]:
    """UN Security Council Consolidated List — XML."""
    entries: list[Entry] = []
    root = ET.fromstring(raw)
    for tag, kind in (("INDIVIDUALS/INDIVIDUAL", "individual"), ("ENTITIES/ENTITY", "entity")):
        for node in root.findall(tag):
            parts = [node.findtext(f) for f in
                     ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME")]
            name = " ".join(p.strip() for p in parts if p and p.strip())
            if not name:
                name = (node.findtext("FIRST_NAME") or "").strip()
            if not name:
                continue
            listed = node.findtext("UN_LIST_TYPE") or node.findtext("REFERENCE_NUMBER") or ""
            entries.append(Entry(
                name=name, source="UN Consolidated",
                detail=f"{kind} · {listed}".strip(" ·"),
                url="https://www.un.org/securitycouncil/content/un-sc-consolidated-list",
            ))
    return entries


def parse_generic_csv(raw: bytes) -> list[Entry]:
    """Best-effort parser for a CSV whose first column is a name."""
    entries: list[Entry] = []
    reader = csv.reader(io.StringIO(raw.decode("utf-8", errors="replace")))
    rows = list(reader)
    start = 1 if rows and not rows[0][0].strip()[:1].isalpha() else 0
    for row in rows[start:]:
        if row and row[0].strip():
            entries.append(Entry(name=row[0].strip(), source="custom feed"))
    return entries


PARSERS = {
    "ofac_sdn": parse_ofac_sdn,
    "un": parse_un_consolidated,
    "csv": parse_generic_csv,
}

# feed = "label|url|parser_key"  (parser_key from PARSERS)
DEFAULT_FEEDS = [
    "OFAC SDN|https://www.treasury.gov/ofac/downloads/sdn.csv|ofac_sdn",
    "UN Consolidated|https://scsanctions.un.org/resources/xml/en/consolidated.xml|un",
    # Add Canada SEMA / UK OFSI / EU via OSINT_WATCHLIST_FEEDS (same format).
]


class FreeWatchlists(Connector):
    name = "watchlists_free"
    label = "Free sanctions / PEP / watchlists"
    category = "sanctions"
    free = True
    note = "$0 SoftCheck-equivalent. Fetches official free lists (OFAC, UN, +configurable) and matches locally."

    def _feeds(self) -> list[str]:
        extra = get("OSINT_WATCHLIST_FEEDS")
        feeds = list(DEFAULT_FEEDS)
        if extra:
            feeds += [f.strip() for f in extra.split(";") if f.strip()]
        return feeds

    def _fetch(self, label: str, url: str) -> bytes | None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache = CACHE_DIR / (normalize(label).replace(" ", "_") + url[-4:].strip("."))
        if cache.exists() and (time.time() - cache.stat().st_mtime) < CACHE_TTL:
            return cache.read_bytes()
        resp = self._session().get(url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        cache.write_bytes(resp.content)
        return resp.content

    def load_entries(self) -> tuple[list[Entry], list[str]]:
        entries: list[Entry] = []
        errors: list[str] = []
        for feed in self._feeds():
            try:
                label, url, pkey = (feed.split("|") + ["", "", "csv"])[:3]
                raw = self._fetch(label, url)
                if raw:
                    entries.extend(PARSERS.get(pkey, parse_generic_csv)(raw))
            except Exception as exc:
                errors.append(f"{feed.split('|')[0]}: {exc}")
        return entries, errors

    def search(self, subject: Subject) -> list[Finding]:
        threshold = float(get("OSINT_WATCHLIST_THRESHOLD", "") or DEFAULT_THRESHOLD)
        entries, errors = self.load_entries()
        findings: list[Finding] = []
        seen: set[tuple[str, str]] = set()
        for e in entries:
            s = score(subject.as_query(), e.name)
            if s < threshold:
                continue
            key = (normalize(e.name), e.source)
            if key in seen:
                continue
            seen.add(key)
            findings.append(Finding(
                source=self.name, category=self.category,
                title=f"{e.name} — {e.source}",
                summary=f"⚠ Possible watchlist match ({s:.0%}). {e.detail}",
                url=e.url, confidence="possible" if s < 0.99 else "confirmed",
                data={"match_score": round(s, 3), "list": e.source, "detail": e.detail},
            ))
        findings.sort(key=lambda f: f.data.get("match_score", 0), reverse=True)
        if not findings:
            findings.append(Finding(
                source=self.name, category=self.category,
                title="No watchlist match",
                summary=f"Screened against {len(entries)} listed entries; no name match "
                        f"at ≥{int(threshold*100)}%.",
                confidence="unverified",
                data={"screened": len(entries), "feed_errors": errors},
            ))
        return findings
