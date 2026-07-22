"""Connector registry. Order here = order in the dossier report."""
from __future__ import annotations

from .base import Connector
from .peopledatalabs import PeopleDataLabs
from .pipl import Pipl
from .orgbook_bc import OrgBookBC
from .opencorporates import OpenCorporates
from .opensanctions import OpenSanctions
from .complyadvantage import ComplyAdvantage
from .watchlists_free import FreeWatchlists
from .certn import Certn
from .gdelt import Gdelt
from .username_osint import UsernameOsint
from .manual_sources import ManualSources

ALL_CONNECTORS: list[type[Connector]] = [
    # identity
    Pipl,
    PeopleDataLabs,
    # corporate
    OrgBookBC,
    OpenCorporates,
    # sanctions / PEP
    FreeWatchlists,   # free, keyless — screens official public lists
    OpenSanctions,
    ComplyAdvantage,
    # litigation (consent-gated)
    Certn,
    # adverse media
    Gdelt,
    # social
    UsernameOsint,
    # manual deep-links
    ManualSources,
]


def instances() -> list[Connector]:
    return [cls() for cls in ALL_CONNECTORS]
