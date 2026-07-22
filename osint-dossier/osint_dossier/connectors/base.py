"""Base class for all connectors."""
from __future__ import annotations

from abc import ABC, abstractmethod

import requests

from .. import config
from ..models import Finding, Subject


class Connector(ABC):
    """A single data source. Subclasses implement `search`."""

    name: str = "base"
    label: str = "Base connector"
    category: str = "identity"
    #: True if it works with no API key.
    free: bool = True
    #: Short note shown in the report / status.
    note: str = ""

    def enabled(self) -> bool:
        return config.is_enabled(self.name)

    def _session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update({"User-Agent": config.USER_AGENT, "Accept": "application/json"})
        return s

    @abstractmethod
    def search(self, subject: Subject) -> list[Finding]:
        """Query the source and return a list of Findings. May raise."""
        raise NotImplementedError
