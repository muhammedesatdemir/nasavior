# Data Provenance

All values were transcribed by hand from the NASA documents listed in `references.json`.
Nothing is estimated, interpolated or generated. Fields a source does not state are empty (null).

| File | How it was made |
|---|---|
| `investigations.json` | `scripts/build_investigations.py`. Name, platform, hardware, objective copied from NASA PSI metadata (`data/raw/psi_investigations_*.json`, fetched 2026-11-14). `key_findings` written only from pages we read, each with ref_id + page. Theme tags are Nasavior's own classification, not NASA statements. |
| `measurements.csv` | `scripts/build_measurements.py`. Each row has ref_id + page/table. Sources: Olson & Ferkul 2012 Table I; BASS-II poster p.18; Saffire I-III Table I; Saffire IV/V Tables 1-2; Saffire VI Table 1. All tier A (printed values). |
| `environments.yaml` | Preset values with basis ref + page. `assumption: true` where sources do not define the environment (Mars habitat, rover). Lunar/rover lines (O2 >= 30%, <= 10.2 psi; exploration atmosphere 8.2 psi / 34% O2) were confirmed by the team against the challenge brief and the NASA Exploration Atmosphere design reference. |
| `references.json` | NTRS records verified to exist with public PDF on 2026-11-14; PSI records generated from the metadata dump. |

## Known limitations
- Reduced-gravity limits (0.16 g, 0.38 g) come only from drop-tower tests (5.18 s) with criteria that differ from 1g (stated by the source).
- Saffire I-III Table I gives no pressure; left null.
- Saffire VI per-sample heat release/CO/CO2 columns were garbled in text extraction and are not transcribed.
- PSI investigation URLs follow the PSI web-app route `/physci/repo/data/investigation/<id>`; the page is JavaScript-rendered so the link could not be tested without a browser.
- PSI start/end dates are not used (some look inconsistent, e.g. SAFFIRE-I).
- Olson & Ferkul 2012 states in its Conclusions that Martian limits were "up to 5.75% O2 lower" than 1 g, but its Table I shows 5.75 is the Lunar value for Mylar (the largest Martian value is 3.35). We use Table I and its Eq. 1.
