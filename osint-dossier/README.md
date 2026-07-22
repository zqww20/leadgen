# osint-dossier

A people-focused **OSINT / due-diligence** tool for **Canadian** subjects. You give it a
name (plus any known email/phone/employer/location); it runs every enabled data source
concurrently and assembles a single **dossier** — corporate footprint, litigation leads,
sanctions/PEP hits, adverse media, online presence, and click-through deep-links to the
registries that have no API.

- **Free sources work out of the box** — no keys required.
- **Paid sources activate automatically** the moment you add their API key. Build as you subscribe.
- Runs as a **CLI** or a small **local web app**. The backend makes the calls, so there are no browser CORS problems.

---

## Quick start

```bash
cd osint-dossier
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # optional — add keys for paid sources

# See what's enabled
python -m osint_dossier --status

# Run an investigation (CLI)
python -m osint_dossier "Jane Doe" \
    --province BC --location "Vancouver, BC" \
    --operator you \
    --basis "corporate due diligence, engagement #1234"

# ...or use the web UI
python -m osint_dossier.web        # http://127.0.0.1:5000
```

Reports are written to `cases/<case_id>/dossier.html` and `dossier.json`.
Open the HTML in a browser — findings are grouped by category and adverse signals are flagged.

---

## Sources, coverage & cost

| Connector | Section | Key needed | Cost |
|---|---|---|---|
| **OrgBook BC** | Corporate | — free | **$0** |
| **GDELT** | Adverse media | — free | **$0** |
| **Username footprint** | Online | — free | **$0** |
| **Manual deep-links** | Registries | — free | **$0** (Corp Canada, ON/QC registries, CanLII, OSB, BC courts) |
| **OpenSanctions** | Sanctions / PEP | `OPENSANCTIONS_API_KEY` *or* self-host `OPENSANCTIONS_BASE_URL` | Free self-hosted; ~€0.10/call hosted |
| **People Data Labs** | Identity | `PDL_API_KEY` | ~$0.20–0.28/match ($98/mo Pro) |
| **Pipl** | Identity | `PIPL_API_KEY` | ~$0.10+/match (investigations-gated) |
| **OpenCorporates** | Corporate | `OPENCORPORATES_API_TOKEN` | from ~£2,250/yr |
| **ComplyAdvantage** | Sanctions / PEP | `COMPLYADVANTAGE_API_KEY` | from ~$99/mo |
| **Certn** | Criminal (consent) | `CERTN_API_KEY` | $24.99–29.99 CAD/check |

Start with the free tier — it gets you ~60% of a dossier at $0. Add paid keys as needed.

---

## The Canadian reality (why it's built this way)

These aren't disclaimers — they're the constraints the tool is designed around:

1. **Criminal records need consent.** There is no open criminal-records API in Canada; CPIC
   checks are consent- and identity-gated. The **Certn** connector will not run unless you pass
   `--consent` *and* a subject email — it emails the subject to collect consent itself. Everything
   else finds only *reported/public* information.
2. **No facial recognition.** The *Clearview AI* ruling (federal + provincial privacy
   commissioners, 2021) found scraping Canadians' faces unlawful under PIPEDA. This tool does
   **not** do face search. Usernames are only checked when you supply them explicitly.
3. **Lawful basis is mandatory.** PIPEDA requires you to justify collecting personal information.
   The tool refuses to run without `--basis`, and logs every run (case id, operator, subject-name
   hash, basis, sources) to `cases/audit.log`.
4. **Licensing.** Investigating people "for reward" typically requires a provincial
   **private-investigator licence** (e.g. Ontario PSISA, BC Security Services Act). That's on you.
5. **Data hygiene.** Generated dossiers contain personal data. `cases/` is git-ignored by default;
   minimize, secure, and delete on a retention schedule (Québec Law 25 is strict).

Findings are **unverified leads** from third-party sources — corroborate before you rely on them,
and keep OSINT output separate from any employment/tenancy/credit decision.

---

## Layout & extending

```
osint_dossier/
  core.py            orchestrator (runs enabled connectors concurrently)
  models.py          Subject / Finding / Dossier
  config.py          reads .env; decides which connectors are enabled
  audit.py           lawful-basis enforcement + audit log
  report.py          JSON + HTML + terminal rendering
  cli.py / web.py    the two front-ends
  connectors/        one module per source (subclass Connector)
  templates/         dossier + web-form HTML
tests/test_offline.py  runs with no network
```

**Add a source:** subclass `Connector` (see `connectors/orgbook_bc.py`), implement `search()` to
return `Finding` objects, register it in `connectors/__init__.py`, and add its key mapping in
`config.KEY_FOR`. It'll appear in `--status` and run automatically when enabled.

```bash
python tests/test_offline.py      # offline sanity check
```
