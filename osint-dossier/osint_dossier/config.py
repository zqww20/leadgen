"""Configuration: reads API keys from the environment / .env file.

Free connectors need no config. Paid connectors are enabled automatically
when their key is present, so the tool grows as you add subscriptions.
"""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:  # dotenv is optional
    pass


def get(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


# Which connectors require a key, and which env var holds it.
# `None` means the connector is free / keyless and always available.
KEY_FOR = {
    "orgbook_bc": None,
    "gdelt": None,
    "username_osint": None,
    "manual_sources": None,
    "watchlists_free": None,                     # free sanctions/PEP via official public lists
    "opensanctions": "OPENSANCTIONS_API_KEY",   # or self-host via OPENSANCTIONS_BASE_URL
    "pipl": "PIPL_API_KEY",
    "peopledatalabs": "PDL_API_KEY",
    "opencorporates": "OPENCORPORATES_API_TOKEN",
    "certn": "CERTN_API_KEY",
    "complyadvantage": "COMPLYADVANTAGE_API_KEY",
}


def is_enabled(connector: str) -> bool:
    """A connector is enabled if it is free, or its key/self-host URL is set."""
    key_var = KEY_FOR.get(connector)
    if key_var is None:
        return True
    if connector == "opensanctions":
        # Enabled by a hosted key OR a self-hosted base URL.
        return bool(get("OPENSANCTIONS_API_KEY") or get("OPENSANCTIONS_BASE_URL"))
    return bool(get(key_var))


def enabled_connectors() -> list[str]:
    return [name for name in KEY_FOR if is_enabled(name)]


def status_report() -> list[dict[str, str]]:
    """Human-readable enable/disable status for every connector."""
    rows = []
    for name, key_var in KEY_FOR.items():
        enabled = is_enabled(name)
        if key_var is None:
            reason = "free / keyless"
        elif enabled:
            reason = f"{key_var} set"
        else:
            reason = f"set {key_var} to enable"
        rows.append({
            "connector": name,
            "enabled": "yes" if enabled else "no",
            "detail": reason,
        })
    return rows


# Network defaults
HTTP_TIMEOUT = int(get("OSINT_HTTP_TIMEOUT", "20") or "20")
USER_AGENT = get(
    "OSINT_USER_AGENT",
    "osint-dossier/1.0 (+research; contact set OSINT_USER_AGENT)",
)
