"""Username footprint — free, keyless social presence check.

Only runs when you explicitly supply a username (--username). It never guesses
usernames from a person's name: auto-enumeration is noisy and privacy-invasive.
Best-effort: many platforms block automated requests, so treat results as leads.
"""
from __future__ import annotations

from .base import Connector
from ..config import HTTP_TIMEOUT
from ..models import Finding, Subject

# {platform: url template}
PLATFORMS = {
    "GitHub": "https://github.com/{u}",
    "Reddit": "https://www.reddit.com/user/{u}",
    "Instagram": "https://www.instagram.com/{u}/",
    "TikTok": "https://www.tiktok.com/@{u}",
    "X / Twitter": "https://x.com/{u}",
    "Telegram": "https://t.me/{u}",
    "Medium": "https://medium.com/@{u}",
    "GitLab": "https://gitlab.com/{u}",
    "Keybase": "https://keybase.io/{u}",
    "Pinterest": "https://www.pinterest.com/{u}/",
}


class UsernameOsint(Connector):
    name = "username_osint"
    label = "Username footprint"
    category = "social"
    free = True
    note = "Best-effort profile existence check. Only runs on explicit --username."

    def search(self, subject: Subject) -> list[Finding]:
        if not subject.usernames:
            return []
        s = self._session()
        s.headers["Accept"] = "text/html,application/xhtml+xml"
        findings: list[Finding] = []
        for username in subject.usernames:
            for platform, tpl in PLATFORMS.items():
                url = tpl.format(u=username)
                try:
                    resp = s.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
                    code = resp.status_code
                except Exception as exc:  # network hiccup on one platform shouldn't kill the run
                    findings.append(Finding(
                        source=self.name, category=self.category,
                        title=f"{platform}: {username}", summary=f"check failed: {exc}",
                        url=url, confidence="unverified",
                        data={"username": username, "platform": platform, "status": "error"},
                    ))
                    continue
                if code == 200:
                    verdict, conf = "likely exists", "possible"
                elif code in (301, 302, 404, 410):
                    verdict, conf = "not found", "unverified"
                else:
                    verdict, conf = f"inconclusive (HTTP {code})", "unverified"
                findings.append(Finding(
                    source=self.name, category=self.category,
                    title=f"{platform}: {username}", summary=verdict,
                    url=url, confidence=conf,
                    data={"username": username, "platform": platform, "http_status": code},
                ))
        # Surface the hits first.
        findings.sort(key=lambda f: f.confidence == "possible", reverse=True)
        return findings
