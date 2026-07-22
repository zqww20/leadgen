"""Tiny local web UI.  Run:  python -m osint_dossier.web  →  http://127.0.0.1:5000

The backend makes the API calls, so there are no browser CORS issues.
"""
from __future__ import annotations

from flask import Flask, render_template_string, request, abort
from pathlib import Path

from . import config, report
from .audit import LawfulBasisError
from .core import investigate
from .models import Subject

app = Flask(__name__)
_INDEX = (Path(__file__).parent / "templates" / "index.html.j2").read_text(encoding="utf-8")


@app.get("/")
def index():
    return render_template_string(_INDEX, status=config.status_report(), result=None, error=None)


@app.post("/run")
def run():
    form = request.form
    subject = Subject(
        name=form.get("name", "").strip(),
        emails=[e.strip() for e in form.get("email", "").split(",") if e.strip()],
        phones=[p.strip() for p in form.get("phone", "").split(",") if p.strip()],
        usernames=[u.strip() for u in form.get("username", "").split(",") if u.strip()],
        location=form.get("location", "").strip(),
        province=form.get("province", "").strip(),
        employer=form.get("employer", "").strip(),
        notes=("CONSENT: asserted by operator" if form.get("consent") else ""),
    )
    try:
        dossier = investigate(
            subject,
            lawful_basis=form.get("basis", ""),
            operator=form.get("operator", "web"),
        )
    except LawfulBasisError as exc:
        return render_template_string(_INDEX, status=config.status_report(), result=None, error=str(exc))

    report.save(dossier)  # persist to cases/
    return report.render_html(dossier)


@app.get("/cases/<case_id>")
def case(case_id: str):
    safe = "".join(ch for ch in case_id if ch.isalnum())
    path = Path(__file__).resolve().parent.parent / "cases" / safe / "dossier.html"
    if not path.exists():
        abort(404)
    return path.read_text(encoding="utf-8")


def main() -> None:
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
