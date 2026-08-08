# pyjhora_batch

Batch-generate Vedic horoscope reports from a CSV or Excel list of birth details —
a thin layer on top of [PyJHora](../src/jhora). Each person yields three files: a
**vector PDF**, a plain-text **report**, and an importable **Jagannatha Hora `.jhd`**.
It reuses PyJHora's astrology engine and never reimplements calculations.

## Runbook — reproducing `reports/` from scratch

Everything below is copy-paste. No other tooling is involved.

**1. One-time setup** (from the repo root, `PyJHora/`):

```bash
python3.12 -m venv ../.venv312          # any Python 3.10+ works
source ../.venv312/bin/activate         # Windows: ..\.venv312\Scripts\activate

pip install -r requirements.txt         # PyJHora's own deps (PyQt6, swisseph, ...)
pip install -e .                        # PyJHora itself, editable — this is what
                                        # puts src/ on sys.path so `import jhora` works
pip install -r pyjhora_batch/requirements.txt   # reportlab + optional extras
```

Verify the environment before going further — this must print a path inside
`src/jhora`, not an error:

```bash
python -c "import jhora; print(jhora.__file__)"
```

**2. Put your people in a CSV** — `partners.csv` at the repo root. Note the
quotes around `date_of_birth`: it contains commas.

```csv
name,date_of_birth,time_of_birth,place,latitude,longitude,timezone,gender
Ravi Kumar,"1985,6,15",10:30:00,"Ujjain, Madhya Pradesh",23.5,75.75,5.5,male
Asha Menon,"2001,11,3",07:15:00,"Chennai, Tamil Nadu",13.0827,80.2707,5.5,female
```

**3. Generate.** This is the exact command that produced the current `reports/`:

```bash
python -m pyjhora_batch partners.csv -o reports/ --dhasa all
```

Takes ~8s per person and writes three files each:

| File | What it is |
|------|-----------|
| `<name>_<dob>.pdf` | ~218-page vector report, ~585 KB, fully searchable |
| `<name>_<dob>.txt` | the same content as plain text, ~750 KB |
| `<name>_<dob>.jhd` | birth-data seed file, opens in Jagannatha Hora |

Plus `batch.log` (full log with tracebacks) and, if any row fails,
`failures.csv` (the bad rows with an `_error` column — fix and re-run just that
file).

**Drop `--dhasa all` for a much shorter report.** It is the only thing standing
between a ~50-page and a ~230-page PDF: with it you get all 60 dhasa systems
(~8,500 period rows), without it just Vimsottari.

```bash
python -m pyjhora_batch partners.csv -o reports/            # ~50 pages, ~155 KB
python -m pyjhora_batch partners.csv -o reports/ --dhasa all --workers auto
```

**4. Check it worked.** The last page of the PDF lists anything that could not
be generated; on a healthy run it is absent entirely. All 60 dhasa systems
should build.

To confirm the whole toolchain, run the tests (150 should pass):

```bash
python -m pytest pyjhora_batch/tests -q
```

## Quick start (CLI)

```bash
# from the repo root
python -m pyjhora_batch people.csv -o reports/
python -m pyjhora_batch people.xlsx -o reports/ --workers auto
python -m pyjhora_batch people.csv -o reports/ --no-pdf      # just .jhd + .txt (fast)
python -m pyjhora_batch people.csv -o reports/ --dhasa all   # every dhasa system
python -m pyjhora_batch people.csv -o reports/ --pdf-mode screenshot   # old Qt capture
```

| Flag | Meaning |
|------|---------|
| `-o, --out-dir DIR` | Output directory (default `reports`). |
| `-w, --workers N`   | Worker processes: integer or `auto` (cpus−1). Default `1`. |
| `--sheet S`         | Excel worksheet name or 0-based index. |
| `--no-pdf` / `--no-jhd` / `--no-txt` | Skip that output type. |
| `--pdf-mode MODE`   | `vector` (default) or `screenshot` — see [Outputs](#outputs). |
| `--dhasa NAME`      | Dhasa system to include; repeatable. `--dhasa all` for every system. Default `vimsottari`. |
| `--expand-all-tabs` | Expand every chart tab (screenshot mode only). |
| `-q, --quiet`       | Only warnings/errors + the final summary. |
| `--allow-failures`  | Exit `0` even if some records fail. |

Exit codes: `0` success · `1` at least one record failed · `2` bad usage / missing input.

## Input format

One row per person. Column names are case-insensitive and accept common aliases
(spaces/hyphens are treated as underscores):

| Field | Required | Format / aliases |
|-------|----------|------------------|
| `date_of_birth` | ✅ | `YYYY,M,D` (e.g. `1985,6,15`) — or a real Excel date cell. Aliases: `dob`, `date`. |
| `time_of_birth` | ✅ | `HH:MM:SS` 24h — or a real Excel time cell. Aliases: `tob`, `time`. |
| `place` / `place_name` | ✅ | Any label. Aliases: `location`, `city`. |
| `latitude`  | ✅ | Decimal degrees, N positive. Alias: `lat`. |
| `longitude` | ✅ | Decimal degrees, E positive. Aliases: `long`, `lon`, `lng`. |
| `timezone`  | ✅ | Hours from UTC, e.g. `5.5`. Aliases: `tz`, `utc_offset`. |
| `name`      |    | Person's name (used in output filenames). |
| `gender`    |    | `0`=Female `1`=Male `2`=Transgender `3`=None, or a label (`male`/`female`/…). Default `3`. |
| `chart_type`|    | `south_indian` (default), `north_indian`, `east_indian`, `western`, `sudarsana_chakra`. |
| `language`  |    | `English` (default), `Hindi`, `Tamil`, `Telugu`, `Kannada`. |
| `output` / `filename` |  | Override the output base filename for that row. |

### Spouse columns (marriage compatibility)

Compatibility is scored from **four numbers only**: each partner's nakshatra and
pada. Everything below exists to obtain the spouse's pair precisely — the
native's is already computed from their own birth data.

There are two ways to supply it. **Prefer the first.**

**A. The spouse's birth details** — exact, and the recommended route:

| Column | Required | Notes |
|--------|----------|-------|
| `spouse_date_of_birth` | ✅ | `YYYY,M,D`. Aliases: `spouse_dob`, `partner_dob`. |
| `spouse_time_of_birth` | ✅ | `HH:MM:SS` 24h. Aliases: `spouse_tob`, `partner_tob`. |
| `spouse_latitude` | ✅ | Decimal degrees, N positive. Alias: `spouse_lat`. |
| `spouse_longitude` | ✅ | Decimal degrees, E positive. Aliases: `spouse_long`, `spouse_lon`. |
| `spouse_timezone` | ✅ | Hours from UTC. Alias: `spouse_tz`. |
| `spouse_place` |  | Label only; not used in the calculation. |

All five ✅ columns must be present together, or this route is skipped.

**B. The spouse's star directly** — when the birth time is unknown:

| Column | Required | Notes |
|--------|----------|-------|
| `spouse_nakshatra` | ✅ | `1`–`27`, or a name (`Swaathi`). Aliases: `spouse_star`, `spouse_nakshathra`. |
| `spouse_pada` | ✅ | `1`–`4`. Aliases: `spouse_paadham`, `spouse_quarter`. |

⚠️ **A guessed birth time makes route B unreliable.** A pada is 3°20′ of Moon
travel ≈ **6 hours**. Get the time wrong by half a day and the pada — and with
it varna, vasiya, rajju and sthree-dheerga — can all change.

**Applies to both routes:**

| Column | Required | Notes |
|--------|----------|-------|
| `spouse_name` |  | Shown in the report; not used in the calculation. |
| `spouse_gender` |  | Which partner is the "boy" changes several kootas, so it is not arbitrary. Defaults to the opposite of `gender`; set this only for a same-sex pair or when `gender` is blank. |
| `compatibility_method` |  | `north` (Ashtakoota, out of 36) or `south` (10 poruthams). Defaults from `chart_type`: `south_indian` → south, otherwise north. |

Omit every spouse column and the section is simply absent — it is never an error.

Example:

```csv
name,date_of_birth,time_of_birth,place,latitude,longitude,timezone,gender,spouse_name,spouse_dob,spouse_tob,spouse_place,spouse_lat,spouse_long,spouse_tz
Ravi Kumar,"1985,6,15",10:30:00,Ujjain,23.5,75.75,5.5,male,Latha Menon,"1988,2,9",18:20:00,Jaipur,26.9124,75.7873,5.5
```

The report then carries a **Marriage Compatibility** section showing both stars,
which one was treated as the boy, how the spouse's star was obtained, the
per-koota (or per-porutham) breakdown and the total.

Example (`people.csv`):

```csv
name,date_of_birth,time_of_birth,place,latitude,longitude,timezone,gender
Test Person,"1985,6,15",10:30:00,Ujjain,23.5,75.75,5.5,male
Asha Rao,"1985,11,2",08:15:00,Chennai,13.0878,80.2785,5.5,female
```

See `pyjhora_batch/examples/` for sample `.csv` and `.xlsx`.

## Outputs

For each valid row (filename derived from name + DOB, de-duplicated):

- `<name>_<dob>.pdf` — the full horoscope report.
- `<name>_<dob>.txt` — the same content as plain text, for reading/grepping/pasting.
- `<name>_<dob>.jhd` — importable into Jagannatha Hora.

### PDF modes

`--pdf-mode vector` (default) extracts the report data from PyJHora's engine and
typesets it with ReportLab. `--pdf-mode screenshot` is PyJHora's original path:
`ChartTabbed.save_as_pdf` grabs each Qt tab as a bitmap and pastes two per A4 page.

| | vector | screenshot |
|---|---|---|
| Text | real, selectable, searchable | pixels (16–45 chars/page, all of it tab titles) |
| Resolution | vector — sharp at any zoom | ~975×770 JPEG ≈ **130 DPI**, upscaled 1.12× |
| Size (default settings) | **~155 KB / ~50 pages** | ~10 MB / 38 pages |
| Speed | ~2 s/person | ~60 s/person |
| Needs Qt | no | yes (offscreen `QApplication`) |
| Chart diagrams | drawn as vector lines | drawn as bitmaps |

`vector` is better on every axis; `screenshot` exists only as a fallback.

### Chart diagrams

All 23 divisional charts plus the bhava chart are drawn as real diagrams — in
the PDF as vector lines, in the text report as an ASCII grid. The style follows
each row's `chart_type` column:

- **`south_indian`** (default) — the 4×4 ring with an open centre, signs in
  fixed cells (Pisces top-left, running clockwise), lagna marked with a
  diagonal stroke in its corner.
- **`north_indian`** — the square with both diagonals and the diamond on the
  edge midpoints; houses are fixed and signs rotate so house 1 (marked *Lagna*)
  is always the top kite.

Cell layouts are taken from `SouthIndianChart._zodiac_symbols` and
`NorthIndianChart._north_label_positions` in `jhora/ui/chart_styles.py`, so they
match the conventions the GUI draws. Other styles (`east_indian`, `western`)
fall back to the South Indian layout and say so in a note on the section.

The text report always uses the South Indian ASCII grid — it is the one layout
that survives in fixed-width text — and annotates every cell with its house
number, so North Indian readers still get the house sequence:

```
+----------------------+----------------------+----------------------+----------------------+
| Pi H8                | Ar H9                | Ta H10               | Ge H11               |
|                      | Sun☉                 |                      | Jupiter♃             |
|                      | Mercury☿             |                      |                      |
+----------------------+----------------------+----------------------+----------------------+
| Aq H7                |                                             | Cn H12               |
| Mars♂                |                                             | Kethu☋               |
| Venus♀               |                                             |                      |
+----------------------+                                             +----------------------+
| Cp H6                |                                             | Le H1 <              |
| Moon☾                |                                             | Ascendantℒ           |
```

### Report contents

Both the text and vector-PDF renderers read the same structured `Report`
(`report_data.py`), ~85 sections in all:

- birth details and panchanga at birth
- raja yogas, yogas, doshas, general predictions
- ashtakavarga (bhinna + sarva)
- sphuta (14 special points), shad bala, bhava bala, harsha/pancha/dwadhasa
  vargeeya bala, vimsopaka bala, vaiseshikamsa bala
- the bhava (house) chart, drawn, plus a cusp table with begin/middle/end degrees
- dhasa-bhukthi periods — all 60 systems with `--dhasa all` (see below)
- planetary positions and arudha padas per chart, and drawn diagrams for all
  23 divisional charts

- marriage compatibility, when the [spouse columns](#spouse-columns-marriage-compatibility)
  are supplied

Not included: **pancha pakshi**, which the GUI computes for *today* rather than
the birth moment.
A section that fails is recorded under "Sections that could not be generated"
rather than aborting the report.

Per run, in the output directory:

- `batch.log` — full log incl. stack traces for failed rows.
- `failures.csv` — every invalid/failed row with `_row/_line/_status/_error` plus its
  original columns, so you can fix and re-run just that file.

## Python API

```python
from pyjhora_batch import build_report, render_pdf, write_text, run_csv, BirthRecord

rec = BirthRecord.from_dict({
    "name": "Test Person", "date_of_birth": "1985,6,15", "time_of_birth": "10:30:00",
    "place_name": "Ujjain", "latitude": 23.5, "longitude": 75.75, "timezone": 5.5,
})

# extract once, render twice
report = build_report(rec)                 # ~0.6s, no Qt
write_text(rec, "reports/test.txt", report=report)
render_pdf(report, "reports/test.pdf")

for section in report.sections:            # walk the structured data yourself
    print(section.title, len(section.pairs), len(section.rows))
print(report.warnings)                     # sections that could not be built
```

The legacy screenshot PDF is still one call:

```python
from pyjhora_batch import generate_pdf

generate_pdf({
    "name": "Test Person", "date_of_birth": "1985,6,15", "time_of_birth": "10:30:00",
    "place_name": "Ujjain", "latitude": 23.5, "longitude": 75.75, "timezone": 5.5,
    "gender": "male",
}, "reports/screenshot.pdf")
```

Batch:

```python
summary = run_csv("people.csv", "reports/", workers=4)
print(summary)                       # Batch summary: N/M succeeded, K failed
for r in summary.failures:
    print(r.row_number, r.error)
```

## The `.jhd` format (important caveat)

PyJHora has no native `.jhd` export; `jhd_writer.py` is a fresh serializer,
calibrated against a real file exported by the Jagannatha Hora Windows app. Its
encoding is deliberately inconsistent, and matching it matters:

- **Line 5 (timezone) is packed `H.MM`** — `+5:30` → `-5.300000`.
- **Lines 9/10 repeat that timezone as plain decimal** — `-5.500000`. The same
  value appearing both ways in one file is what proves the format is not packed
  throughout.
- **Longitude/latitude are decimal degrees**, not `D.MMSS`.
- **Time is decimal hours with 15 decimals** — `00:00` → `0.000000000000000`.
- Signs are inverted from the usual: timezone and longitude **negative for East**,
  latitude positive for North.

Still unconfirmed: line 12 is `105` in the reference export and `0` here (purpose
unknown; harmless since lat/long/tz are explicit), and CRLF vs LF line endings.

## Performance

In the default `vector` mode a person costs ~2s for all three files (~0.6s to
compute the report, ~1.5s to typeset the PDF); the `.jhd` write is instant.
Measured: 2 people × 3 outputs in **4.6s** end to end, including interpreter and
ephemeris startup.

`--pdf-mode screenshot` is far slower — ~25–40s per PDF, dominated by the Qt save
step. `--workers N` spreads records across `N` processes (the pool uses `spawn`);
workers only create an offscreen `QApplication` when screenshot mode needs one.

## Known PyJHora caveats

- **Headless fix required.** Driving `ChartTabbed` without the GUI needs two fixes
  in `src/jhora/ui/horo_chart_tabs.py` (a `config` import and two `self._horo is None`
  guards). These are committed on branch `fix/headless-compute-horoscope`.
- **Constructor ignores birth-detail kwargs.** `ChartTabbed(date_of_birth=…, …)` does
  not apply those values (it defaults to *now* + IP location). The wrapper instead
  injects them via the public setters with networking disabled — so batch output is
  deterministic and uses each row's own coordinates. Note that some screenshot-mode
  tabs (e.g. Pancha Pakshi) still render *today* at the IP-guessed location; the
  vector report is built from the birth data only and has no such leak.
- **`jhora.horoscope.main` is stale — use `jhora.horoscope.info`.** `main.Horoscope`
  raises on construction (`get_calendar_information` calls `drik.vaara(jd)` against a
  two-argument signature). `info.Horoscope` is what the GUI actually imports.
- **Set the ayanamsa before any headless engine call.** `ChartTabbed.__init__` runs
  `drik.set_ayanamsa_mode(const._DEFAULT_AYANAMSA_MODE)`; skip it and swisseph keeps
  its own default sidereal mode, so every longitude — and therefore tithi, nakshatra,
  yoga and all divisional charts — silently disagrees with the GUI. `build_report`
  does this for you.
- **Engine globals are order-sensitive.** Calling predictions → dosha → yoga →
  raja_yoga in one process makes `raja_yoga` raise `IndexError`, while any shorter
  prefix works. `report_data` orders the calls defensively and isolates each section.

## Tests

```bash
python -m pytest pyjhora_batch/tests -q                 # fast: no PDF render
PYJHORA_TEST_PARALLEL=1 python -m pytest pyjhora_batch/tests   # also the spawn-pool test
```
