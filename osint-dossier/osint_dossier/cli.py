"""Command-line interface.

    python -m osint_dossier "Jane Doe" --province BC \
        --basis "corporate due diligence, engagement #1234"
"""
from __future__ import annotations

import argparse
import sys

from . import config, report
from .audit import LawfulBasisError
from .core import investigate
from .models import Subject


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="osint_dossier",
        description="Assemble an OSINT / due-diligence dossier on a person (Canada-focused).",
    )
    p.add_argument("name", nargs="?", help="Subject full name")
    p.add_argument("--basis", default="", help="Lawful basis for the search (REQUIRED to run)")
    p.add_argument("--operator", default="", help="Who is running this (for the audit log)")
    p.add_argument("--email", action="append", default=[], help="Known email (repeatable)")
    p.add_argument("--phone", action="append", default=[], help="Known phone (repeatable)")
    p.add_argument("--username", action="append", default=[], help="Known username (repeatable)")
    p.add_argument("--alias", action="append", default=[], help="Known alias (repeatable)")
    p.add_argument("--location", default="", help='Free-text locality, e.g. "Vancouver, BC"')
    p.add_argument("--province", default="", help="Province code, e.g. BC, ON, QC")
    p.add_argument("--employer", default="", help="Known employer / company")
    p.add_argument("--dob", default="", help="Date of birth (optional)")
    p.add_argument("--only", default="", help="Comma-separated connector names to run")
    p.add_argument("--consent", action="store_true",
                   help="Assert the subject's informed consent (unlocks Certn criminal check)")
    p.add_argument("--status", action="store_true", help="Show connector enable/disable status and exit")
    return p


def _print_status() -> None:
    print("\n  Connector status (set keys in .env to enable paid sources):\n")
    for row in config.status_report():
        mark = "✓" if row["enabled"] == "yes" else "·"
        print(f"   {mark} {row['connector']:<16} {row['detail']}")
    print()


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.status:
        _print_status()
        return 0

    if not args.name:
        print("error: subject name is required (or use --status).", file=sys.stderr)
        return 2

    subject = Subject(
        name=args.name, aliases=args.alias, emails=args.email, phones=args.phone,
        usernames=args.username, location=args.location, province=args.province,
        employer=args.employer, dob=args.dob,
        notes=("CONSENT: asserted by operator" if args.consent else ""),
    )
    only = [c.strip() for c in args.only.split(",") if c.strip()] or None

    def progress(name: str, status: str) -> None:
        if status == "start":
            print(f"   … {name}", file=sys.stderr)
        else:
            print(f"   ✓ {name}: {status}", file=sys.stderr)

    try:
        dossier = investigate(
            subject, lawful_basis=args.basis, operator=args.operator,
            only=only, progress=progress,
        )
    except LawfulBasisError as exc:
        print(f"\nerror: {exc}\n", file=sys.stderr)
        return 2

    print(report.terminal_summary(dossier))
    paths = report.save(dossier)
    print(f"  report saved:\n    {paths['html']}\n    {paths['json']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
