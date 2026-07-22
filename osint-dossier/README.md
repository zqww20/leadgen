# osint-dossier

A **person-intelligence / background-check** tool for **Canadian** subjects — it connects
many data sources into one dossier. You give it a name (plus any known
email/phone/employer/location); it runs every enabled source concurrently and assembles a
single report — corporate footprint, litigation leads, sanctions/PEP hits, adverse media,
online presence, and click-through deep-links to the registries that have no API.

It's built to replace most of a paid background-check service (e.g. Certn) with free
public sources — see **[Doing Certn's checks for free](#doing-certns-checks-for-free)** and
run `python -m osint_dossier --coverage`.

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

# See what's enabled, and what it covers vs Certn's paid catalogue
python -m osint_dossier --status
python -m osint_dossier --coverage

# Run an investigation (CLI). Add --verify-pack for the DIY verification paperwork.
python -m osint_dossier "Jane Doe" \
    --province BC --location "Vancouver, BC" \
    --operator you \
    --basis "corporate due diligence, engagement #1234" \
    --verify-pack

# ...or use the web UI
python -m osint_dossier.web        # http://127.0.0.1:5000
```

Reports are written to `cases/<case_id>/dossier.html` and `dossier.json`.
Open the HTML in a browser — findings are grouped by category and adverse signals are flagged.

---

## Sources, coverage & cost

| Connector | Section | Key needed | Cost |
|---|---|---|---|
| **Free watchlists** | Sanctions / PEP | — free | **$0** (OFAC + UN + configurable Canada/UK/EU) |
| **OrgBook BC** | Corporate | — free | **$0** |
| **GDELT** | Adverse media | — free | **$0** |
| **Username footprint** | Online | — free | **$0** |
| **Manual deep-links** | Registries | — free | **$0** (Corp Canada, ON/QC registries, CanLII, OSB, BC courts, Canada411) |
| **OpenSanctions** | Sanctions / PEP | `OPENSANCTIONS_API_KEY` *or* self-host `OPENSANCTIONS_BASE_URL` | Free self-hosted; ~€0.10/call hosted |
| **People Data Labs** | Identity | `PDL_API_KEY` | ~$0.20–0.28/match ($98/mo Pro) |
| **Pipl** | Identity | `PIPL_API_KEY` | ~$0.10+/match (investigations-gated) |
| **OpenCorporates** | Corporate | `OPENCORPORATES_API_TOKEN` | from ~£2,250/yr |
| **ComplyAdvantage** | Sanctions / PEP | `COMPLYADVANTAGE_API_KEY` | from ~$99/mo |
| **Certn** | Criminal (consent) | `CERTN_API_KEY` | $24.99–29.99 CAD/check |

Start with the free tier — it gets you most of a dossier at $0. Add paid keys as needed.

---

## Doing Certn's checks for free

Certn's value is bundling + automating + the consent plumbing — not secret data. Most of its
catalogue is public data you can pull yourself. `--coverage` prints this map:

| Certn product | Certn price | How this tool does it | Verdict |
|---|---|---|---|
| SoftCheck / Public Records | $9.99 | `watchlists_free` + `gdelt` | **Free** |
| Social Media Check | $59.99 | `username_osint` + manual links | Free (manual) |
| Employment / Education / Credential | $29.99 ea. | `--verify-pack` (+ public registers) | Free (DIY) |
| Reference Check (digital) | $4.49 | `--verify-pack` | Free (DIY) |
| Criminal record *leads* | — | CanLII / court deep-links | Free (partial) |
| OneID identity verification | $4.99 | cheap vendors (Didit ~$0.33) | Cheap |
| **Criminal Record Check (CPIC)** | $24.99 | `certn` (consent) | **Must pay — law** |
| **Credit Report** | $12.99 | `certn` / bureau (consent) | **Must pay — law** |
| **Driver's Abstract / MVR** | $35.99 | provincial (consent) | **Must pay — law** |

The three "must pay" checks are locked behind **consent + a regulated channel** by law — there
is no legal free path, and Certn's per-check price is about what doing it properly costs anyway.

**`--verify-pack`** writes a consent form + employment/education/credential/reference
questionnaires (with ready-to-send emails) into the case folder — the free DIY version of
Certn's $29.99 verification products.

**Free watchlists:** the `watchlists_free` connector fetches official public lists (US OFAC,
UN by default) and fuzzy-matches the name locally — no key. Add more via `.env`:

```bash
OSINT_WATCHLIST_FEEDS="Canada SEMA|https://.../sema.csv|csv;UK OFSI|https://.../ConList.csv|csv"
```

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
  verification.py    --verify-pack generator (consent form + questionnaires)
  cli.py / web.py    the two front-ends
  connectors/        one module per source (subclass Connector)
    watchlists_free.py   free OFAC/UN/... sanctions matcher (stdlib only)
  templates/         dossier + web-form HTML
tests/test_offline.py  runs with no network
```

**Add a source:** subclass `Connector` (see `connectors/orgbook_bc.py`), implement `search()` to
return `Finding` objects, register it in `connectors/__init__.py`, and add its key mapping in
`config.KEY_FOR`. It'll appear in `--status` and run automatically when enabled.

```bash
python tests/test_offline.py      # offline sanity check
```
