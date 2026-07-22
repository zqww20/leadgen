"""Orchestrator: run every enabled connector for a subject, build a Dossier."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from . import audit
from .connectors import instances
from .models import Dossier, Subject


def investigate(
    subject: Subject,
    *,
    lawful_basis: str,
    operator: str,
    only: list[str] | None = None,
    progress: Callable[[str, str], None] | None = None,
) -> Dossier:
    """Run the investigation.

    `only` optionally restricts to a subset of connector names.
    `progress(name, status)` is called as each connector starts/finishes.
    """
    basis = audit.require_basis(lawful_basis)  # raises if missing/too short
    dossier = Dossier(subject=subject, lawful_basis=basis, operator=operator)

    conns = [c for c in instances() if c.enabled()]
    if only:
        conns = [c for c in conns if c.name in only]

    def _run(conn):
        if progress:
            progress(conn.name, "start")
        try:
            return conn.name, conn.search(subject), None
        except Exception as exc:  # one source failing must not sink the dossier
            return conn.name, [], f"{type(exc).__name__}: {exc}"

    # Connectors are independent network calls -> run them concurrently.
    with ThreadPoolExecutor(max_workers=min(8, len(conns) or 1)) as pool:
        futures = [pool.submit(_run, c) for c in conns]
        for fut in as_completed(futures):
            name, findings, error = fut.result()
            dossier.connectors_run.append(name)
            for f in findings:
                dossier.add(f)
            if error:
                dossier.add_error(name, error)
            if progress:
                progress(name, f"error: {error}" if error else f"{len(findings)} finding(s)")

    audit.record(
        case_id=dossier.case_id, operator=operator, subject_name=subject.name,
        lawful_basis=basis, connectors=dossier.connectors_run,
    )
    return dossier
