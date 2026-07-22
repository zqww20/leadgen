"""Offline tests — exercise assembly, rendering, audit and the no-network
connector without touching any external API. Run either:

    python tests/test_offline.py
    python -m pytest tests/
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from osint_dossier import config, report, verification  # noqa: E402
from osint_dossier.audit import LawfulBasisError, require_basis  # noqa: E402
from osint_dossier.connectors.manual_sources import ManualSources  # noqa: E402
from osint_dossier.connectors import watchlists_free as wf  # noqa: E402
from osint_dossier.models import Dossier, Finding, Subject  # noqa: E402


def test_lawful_basis_enforced():
    for bad in ["", "  ", "short"]:
        try:
            require_basis(bad)
        except LawfulBasisError:
            continue
        raise AssertionError(f"expected LawfulBasisError for {bad!r}")
    assert require_basis("corporate due diligence #1234") == "corporate due diligence #1234"


def test_manual_sources_offline():
    findings = ManualSources().search(Subject(name="Jane Doe", province="BC"))
    assert findings, "manual sources should always return deep-links"
    assert all(f.url.startswith("http") for f in findings)
    assert any("canlii" in f.url.lower() for f in findings)


def test_free_connectors_enabled_by_default():
    enabled = config.enabled_connectors()
    for free in ("orgbook_bc", "gdelt", "username_osint", "manual_sources"):
        assert free in enabled, f"{free} should be enabled without a key"


def test_dossier_render_and_save():
    d = Dossier(subject=Subject(name="Jane Doe", location="Vancouver, BC"),
                lawful_basis="unit test", operator="pytest")
    d.connectors_run = ["manual_sources", "gdelt"]
    d.add(Finding(source="gdelt", category="adverse_media",
                  title="Local exec charged with fraud", summary="⚠ Adverse signal: charged, fraud",
                  url="https://example.com/a", confidence="possible",
                  data={"adverse_terms": ["charged", "fraud"]}))
    d.add(Finding(source="manual_sources", category="manual",
                  title="CanLII", url="https://www.canlii.org/", summary="litigation search"))

    html = report.render_html(d)
    assert "Jane Doe" in html and "Adverse Media" in html and "charged" in html

    with tempfile.TemporaryDirectory() as tmp:
        paths = report.save(d, out_dir=Path(tmp))
        assert paths["html"].exists() and paths["json"].exists()
        assert "Jane Doe" in paths["html"].read_text(encoding="utf-8")

    summary = report.terminal_summary(d)
    assert "Jane Doe" in summary and d.case_id in summary


def test_watchlist_scoring():
    assert wf.score("John Smith", "SMITH, John") == 1.0          # token-order invariant
    assert wf.score("Jose Ramirez", "José Ramírez") == 1.0        # accent-fold
    assert wf.score("John Smith", "John Smith Jr") >= 0.9         # subset containment
    assert wf.score("John Smith", "Vladimir Petrov") < 0.6        # unrelated


def test_watchlist_parsers():
    sdn = b'1,"SMITH, John","individual","UKRAINE-EO13662","-0-"\n2,"ACME LTD","entity","IRAN","-0-"'
    entries = wf.parse_ofac_sdn(sdn)
    assert len(entries) == 2 and entries[0].name == "SMITH, John"

    un = (b'<CONSOLIDATED_LIST><INDIVIDUALS>'
          b'<INDIVIDUAL><FIRST_NAME>John</FIRST_NAME><SECOND_NAME>Smith</SECOND_NAME>'
          b'<UN_LIST_TYPE>Al-Qaida</UN_LIST_TYPE></INDIVIDUAL>'
          b'</INDIVIDUALS><ENTITIES></ENTITIES></CONSOLIDATED_LIST>')
    ue = wf.parse_un_consolidated(un)
    assert ue and ue[0].name == "John Smith"


def test_verification_pack():
    with tempfile.TemporaryDirectory() as tmp:
        written = verification.generate(Subject(name="Jane Doe", employer="ACME"), Path(tmp))
        assert len(written) == 5
        consent = next(p for p in written if "consent" in p.name).read_text(encoding="utf-8")
        assert "Jane Doe" in consent and "PIPEDA" in consent


def _run_all():
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
            passed += 1
    print(f"\n{passed} passed")


if __name__ == "__main__":
    _run_all()
