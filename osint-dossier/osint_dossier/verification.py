"""Verification pack generator — the free DIY equivalent of Certn's
$29.99 Employment / Education / Credential verifications and Reference Checks.

Certn charges for the *legwork* (contacting employers/schools/references), not
for secret data. This produces the paperwork to do it yourself: a PIPEDA consent
form the subject signs, plus ready-to-send questionnaires/emails for each source.
"""
from __future__ import annotations

from pathlib import Path

from .models import Subject


def _consent_form(s: Subject) -> str:
    return f"""# Consent to Verify Background Information

I, **{s.name}**, authorize the requesting party to contact the organizations
and references listed below, and to collect and verify information about my
employment, education, professional credentials, and character, for the purpose
of due diligence / screening.

I understand this consent is given under Canada's *Personal Information Protection
and Electronic Documents Act* (PIPEDA) and applicable provincial privacy law, that
I may withdraw it in writing, and that collected information will be used only for
the stated purpose and retained no longer than necessary.

- Full name: {s.name}
- Other names / aliases: {", ".join(s.aliases) or "________________"}
- Date of birth: {s.dob or "________________"}
- Email: {(s.emails or ["________________"])[0]}
- Phone: {(s.phones or ["________________"])[0]}

Signature: ______________________________   Date: ____________________
"""


def _employment(s: Subject) -> str:
    return f"""# Employment Verification — {s.name}

**Email to send to the employer's HR / manager:**

> Subject: Employment verification request — {s.name}
>
> Hello,
>
> With the attached signed consent from {s.name}, we are verifying their
> employment history. Could you please confirm the following? A one-line reply is fine.
>
> 1. Job title held: ____________________
> 2. Employment dates (from / to): ____________________
> 3. Was employment full-time / part-time / contract? ____________________
> 4. Eligible for rehire? (optional) ____________________
> 5. Reason for leaving (if you're able to share): ____________________
>
> Thank you.

Employer: {s.employer or "____________________"}
Contact / phone / email: ____________________
Result (Verified / Partially / Discrepancy): ____________________
"""


def _education(s: Subject) -> str:
    return f"""# Education Verification — {s.name}

**Contact the institution's Registrar (most have a verification office/email).**

> Subject: Degree/credential verification — {s.name}
>
> Hello,
>
> With {s.name}'s signed consent (attached), please confirm:
>
> 1. Credential awarded (degree/diploma/certificate): ____________________
> 2. Program / field of study: ____________________
> 3. Dates of attendance / graduation date: ____________________
> 4. Was the credential completed / conferred? ____________________
>
> Thank you.

Institution: ____________________
Registrar contact: ____________________
Note: Many schools route this through the National Student Clearinghouse (US) or
their own paid verification portal — small fees may apply on their side.
Result: ____________________
"""


def _credential(s: Subject) -> str:
    return f"""# Credential / Licence Verification — {s.name}

Many Canadian professional bodies publish a **free public register** — check
there first (e.g. provincial law societies, engineering (PEO/EGBC), nursing
colleges, accounting bodies, trade certifications).

> Subject: Professional credential verification — {s.name}
>
> Please confirm the status, registration number, and good-standing dates of the
> credential disclosed by {s.name}: ____________________

Issuing body: ____________________
Public register URL (if any): ____________________
Registration #: ____________  Status: ____________  Good standing? ________
"""


def _reference(s: Subject) -> str:
    return f"""# Reference Check — {s.name}

Send to each supplied reference (email = the free "Digital" equivalent).

> Subject: Reference request for {s.name}
>
> Hello, {s.name} listed you as a reference. Would you mind answering briefly?
>
> 1. How do you know {s.name}, and for how long?
> 2. In what capacity did you work together?
> 3. Strengths / areas of growth?
> 4. Would you work with them again? Why / why not?
> 5. Anything else we should know?
>
> Thank you for your time.

Reference name / relationship: ____________________
Response received (date): ____________  Notes: ____________________
"""


SECTIONS = {
    "00_consent_form.md": _consent_form,
    "01_employment_verification.md": _employment,
    "02_education_verification.md": _education,
    "03_credential_verification.md": _credential,
    "04_reference_check.md": _reference,
}


def generate(subject: Subject, out_dir: Path) -> list[Path]:
    """Write the verification pack into out_dir/verifications/ and return paths."""
    vdir = out_dir / "verifications"
    vdir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, builder in SECTIONS.items():
        path = vdir / filename
        path.write_text(builder(subject), encoding="utf-8")
        written.append(path)
    return written
