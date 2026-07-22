"""Render a Dossier to JSON, standalone HTML, and a terminal summary."""
from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import CATEGORIES, Dossier

_TEMPLATES = Path(__file__).resolve().parent / "templates"
_CASES = Path(__file__).resolve().parent.parent / "cases"

CATEGORY_LABELS = {
    "identity": "Identity & Contact",
    "corporate": "Corporate Footprint",
    "litigation": "Litigation & Records",
    "sanctions": "Sanctions / PEP",
    "adverse_media": "Adverse Media",
    "social": "Online Footprint",
    "manual": "Manual Sources (deep-links)",
}

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES)),
    autoescape=select_autoescape(["html"]),
)


def render_html(dossier: Dossier) -> str:
    tpl = _env.get_template("dossier.html.j2")
    return tpl.render(
        d=dossier, grouped=dossier.by_category(),
        categories=CATEGORIES, labels=CATEGORY_LABELS,
    )


def save(dossier: Dossier, out_dir: Path | None = None) -> dict[str, Path]:
    case_dir = (out_dir or _CASES) / dossier.case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    json_path = case_dir / "dossier.json"
    html_path = case_dir / "dossier.html"
    json_path.write_text(json.dumps(dossier.to_dict(), indent=2), encoding="utf-8")
    html_path.write_text(render_html(dossier), encoding="utf-8")
    return {"json": json_path, "html": html_path, "dir": case_dir}


def terminal_summary(dossier: Dossier) -> str:
    lines = [
        "",
        f"  CASE {dossier.case_id}   subject: {dossier.subject.name}",
        f"  basis: {dossier.lawful_basis}",
        f"  ran {len(dossier.connectors_run)} connector(s), "
        f"{len(dossier.findings)} finding(s), {len(dossier.errors)} error(s)",
        "  " + "-" * 56,
    ]
    grouped = dossier.by_category()
    for cat in CATEGORIES:
        items = grouped.get(cat, [])
        if not items:
            continue
        lines.append(f"  [{CATEGORY_LABELS[cat]}] ({len(items)})")
        for f in items[:8]:
            flag = "⚠ " if f.data.get("adverse_terms") or f.confidence == "possible" else "  "
            lines.append(f"    {flag}{f.title[:80]}")
            if f.url:
                lines.append(f"        {f.url[:90]}")
        if len(items) > 8:
            lines.append(f"    ... +{len(items) - 8} more (see HTML report)")
    if dossier.errors:
        lines.append("  " + "-" * 56)
        lines.append("  errors:")
        for e in dossier.errors:
            lines.append(f"    {e['source']}: {e['message'][:80]}")
    lines.append("")
    return "\n".join(lines)
