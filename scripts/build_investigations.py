"""Builds data/investigations.json and merges PSI references into data/references.json.

Inputs : data/raw/psi_investigations_<date>.json (public PSI metadata) + curated overlay below.
Rules  : objective/hardware text is copied from PSI (NASA) and attributed to REF-PSI-xx.
         key_findings are written only from pages we read; each has ref_id + page.
         o2/flow ranges are filled only when a read source states them; otherwise null.
Run    : python scripts/build_investigations.py
"""
import ast
import glob
import json
import pathlib
import re

RAW = sorted(glob.glob("data/raw/psi_investigations_*.json"))[-1]
psi = json.loads(pathlib.Path(RAW).read_text(encoding="utf-8"))

# theme tags are Nasavior's own classification (not a NASA statement)
THEME = {
    "PSI-25": "material_flammability", "PSI-26": "material_flammability", "PSI-98": "material_flammability",
    "PSI-99": "material_flammability", "PSI-100": "material_flammability",
    "PSI-101": "smoke_detection", "PSI-102": "smoke_detection", "PSI-47": "smoke_detection",
    "PSI-115": "smoke_detection",
    "PSI-69": "suppression", "PSI-68": "suppression", "PSI-117": "suppression", "PSI-142": "suppression",
    "PSI-62": "modeling_data_reuse", "PSI-60": "modeling_data_reuse",
    "PSI-10": "fundamental_combustion", "PSI-20": "fundamental_combustion", "PSI-21": "fundamental_combustion",
    "PSI-22": "fundamental_combustion", "PSI-23": "fundamental_combustion", "PSI-39": "fundamental_combustion",
    "PSI-159": "fundamental_combustion", "PSI-106": "fundamental_combustion", "PSI-107": "fundamental_combustion",
}
EQUIP = {  # equipment-guidance relevance (Nasavior classification)
    "material_flammability": "prevention", "smoke_detection": "detection", "suppression": "suppression",
    "fundamental_combustion": "fundamentals", "modeling_data_reuse": "modeling",
}

# verified ranges (only where a read source states them)
RANGES = {
    "PSI-25": dict(o2="13.6-21 (lowest O2 with steady spreading 13.6; ambient 21 and below)", flow="0-55 cm/s",
                   ref="REF-BASS2-POSTER p.7, p.18"),
    "PSI-98": dict(o2="21.5-21.7", flow="20 cm/s", ref="REF-SAFFIRE123 Table I p.29"),
    "PSI-99": dict(o2="22.0-22.1", flow="20-25 cm/s", ref="REF-SAFFIRE123 Table I p.29"),
}

F = lambda text, ref, page: {"text": text, "ref_id": ref, "page_or_figure": page}
FINDINGS = {
    "PSI-25": [
        F("PMMA 1/4 in. rod: steady flame spread was obtained at 13.6% O2 in BASS-II, while the 1g blowoff limit is "
          "16% O2. The source derives a negative oxygen margin of safety of 2.4% O2 and says 1g limits should be "
          "de-rated by at least that much.", "REF-BASS2-POSTER", "p.18"),
        F("The minimum of the flammability boundary lies at very low flow speed, on the order of diffusive flows.",
          "REF-BASS2-POSTER", "p.18-19"),
        F("For 0.1 mm PMMA, radiative quenching was seen when flow velocity went below 2 cm/s, and the flame "
          "neared blow-off as flow approached 40 cm/s.", "REF-BASS2-POSTER", "p.13"),
        F("Normal-gravity PMMA rod blowoff boundary was found to be linear (O2 proportional to flow speed), and "
          "agrees with BASS-II when buoyant stretch and blockage are accounted for.", "REF-MARCUM2016",
          "Abstract (p.1)"),
    ],
    "PSI-98": [
        F("40.6 cm x 94 cm cotton-fiberglass fabric burned in concurrent 20 cm/s flow at 21.7% O2: average spread "
          "1.8 mm/s, about 84 cm burned in 420 s, average flame power 1200 +/- 300 W.", "REF-SAFFIRE123",
          "Table I (p.29), p.17"),
        F("Unlike in 1g, a steady flame was achieved even for a wide sample burning in concurrent flow.",
          "REF-SAFFIRE123", "p.26"),
    ],
    "PSI-99": [
        F("None of the silicone samples (0.27-1.03 mm) spread a flame in microgravity at 20 cm/s, although the "
          "0.27 mm sample was almost always completely consumed in 1g tests.", "REF-SAFFIRE123", "p.11-12"),
        F("Nomex HT90-40, rated safe by the 1g test, could not be ignited even when bathed by a pilot flame.",
          "REF-SAFFIRE123", "p.26"),
        F("Thick PMMA slabs burned with the flame anchored at the sample base (regression 0.01-0.04 mm/s).",
          "REF-SAFFIRE123", "Table I note iv (p.29)"),
    ],
    "PSI-100": [
        F("Saffire-III had the same objective as Saffire-I (large-scale fabric fire) but at a higher flow speed.",
          "REF-SAFFIRE123", "p.4"),
    ],
}

# Experiments that are NOT in PSI but whose NTRS documents we read
NTRS_ONLY = [
    {
        "inv_id": "NTRS-SAFFIRE456", "source": "NTRS", "name": "Saffire IV-VI (Spacecraft Fire Safety Demonstration)",
        "acronym": "Saffire IV-VI", "platform": "Cygnus (free-flying, after ISS departure)",
        "hardware": "Saffire Flow Unit (SFU) and Far Field Diagnostics in Cygnus",
        "objective": "Large-scale flame spread over thin and thick solid fuels at atmospheres including exploration "
                     "environments; impact of the fire on the spacecraft and transport of heat/smoke; "
                     "demonstration of combustion-product measurement and post-fire cleanup systems.",
        "o2_range_pct": "22.0-31.0", "pressure_range_kpa": "54.1-100.0", "flow_range_cm_s": "20",
        "ranges_ref": "REF-SAFFIRE45 Table 1 p.3; REF-SAFFIRE6 Table 1 p.3",
        "key_findings": [
            F("Concurrent flames over thin fuels reach a limiting size in microgravity (contrast with continuous growth "
              "in 1g upward spread); thick PMMA flames also reached an upper flame-length limit.", "REF-SAFFIRE45", "p.8-9"),
            F("Reducing the flow duct height raised the spread rate by about 100% versus Saffire I/III.",
              "REF-SAFFIRE45", "p.8"),
            F("Saffire VI fires of 1.5-3.2 kW in 17-19 m3 of free volume raised CO and CO2 significantly; PMMA tests "
              "exceeded the 1-hour CO2 limit and the 24-hour CO limit, and a typical smoke alarm threshold was reached "
              "only at 981 s.", "REF-SAFFIRE6", "Conclusion"),
        ],
        "ref_ids": ["REF-SAFFIRE45", "REF-SAFFIRE6"], "psi_url": None, "theme": "material_flammability",
        "equipment_theme": "prevention",
    },
    {
        "inv_id": "NTRS-PARTIALG", "source": "NTRS",
        "name": "Partial-gravity flammability studies (drop-tower centrifuge, sounding rocket, planned Moon test)",
        "acronym": "Lunar/Martian-g studies", "platform": "Drop tower; New Shepard sounding rocket; planned lunar surface (FM2)",
        "hardware": "Zero-Gravity Centrifuge (drop tower); LUCI payload on rotating sounding rocket",
        "objective": "Determine material flammability limits at Lunar and Martian gravity and compare to 1g NASA-STD-6001 "
                     "Test 1 and to microgravity forced-flow limits.",
        "o2_range_pct": None, "pressure_range_kpa": None, "flow_range_cm_s": None, "ranges_ref": None,
        "key_findings": [
            F("Martian-gravity limiting oxygen was up to 5.75% O2 lower than normal gravity for the three materials "
              "tested (Mylar, Ultem, Nomex); reduced-g criteria differ from 1g due to 5.18 s drop times.",
              "REF-OLSON2012", "Table I, Conclusions (p.6, p.8)"),
            F("Some materials that do not burn in 1g will burn in 0g with a low-speed flow or in partial gravity such as "
              "Lunar-g. Evidence suggests Lunar gravity could be more hazardous: flame spread rate peaks there and "
              "the oxygen needed for flammability reaches a minimum near Lunar g.",
              "REF-FERKUL2026", "p.1"),
            F("Partial-gravity tests are limited: drop towers give about 5 s and aircraft about 25 s; centrifuges "
              "and the rotating rocket have Coriolis effects.", "REF-FERKUL2026", "p.1"),
            F("LUCI showed that material flammability testing at partial-g is feasible using a spinning vehicle.",
              "REF-LUCI2025", "p.2"),
            F("FM2 plans the first combustion experiments on another world, burning four solid fuel samples in "
              "quiescent habitable atmospheres at actual lunar gravity, with a planned launch in late 2026.",
              "REF-FERKUL2026", "p.1"),
        ],
        "ref_ids": ["REF-OLSON2012", "REF-FERKUL2026", "REF-LUCI2025"], "psi_url": None,
        "theme": "material_flammability", "equipment_theme": "prevention",
    },
]

def clean(t):
    t = (t or "").replace("�", "'")
    return re.sub(r"\s+", " ", t).strip()

def parse_hw(raw):
    if not raw:
        return None
    try:
        d = ast.literal_eval(raw) if isinstance(raw, str) else raw
        names = [d["Name"]] if isinstance(d, dict) else [x.get("Name", "") for x in d]
        return clean("; ".join(n for n in names if n)) or None
    except Exception:
        return clean(str(raw))[:200]

out, psi_refs = [], []
for pid, theme in THEME.items():
    s = psi[pid]
    ref_id = f"REF-{pid}"
    r = RANGES.get(pid, {})
    out.append({
        "inv_id": pid, "source": "PSI", "name": clean(s["Title"]), "acronym": clean(s.get("Acronym")) or None,
        "platform": clean(s.get("Flight Platform")) or None, "hardware": parse_hw(s.get("Experiment Hardware")),
        "objective": clean(s.get("Objectives")),
        "impact": clean(s.get("Research Impacts/Earth Benefits")) or None,
        "o2_range_pct": r.get("o2"), "pressure_range_kpa": None, "flow_range_cm_s": r.get("flow"),
        "ranges_ref": r.get("ref"), "key_findings": FINDINGS.get(pid, []),
        "ref_ids": sorted({ref_id} | {f["ref_id"] for f in FINDINGS.get(pid, [])}),
        "psi_url": f"https://psi.nasa.gov/physci/repo/data/investigation/{pid}",
        "theme": theme, "equipment_theme": EQUIP[theme],
    })
    psi_refs.append({"ref_id": ref_id, "ntrs_id": None, "title": f"NASA PSI investigation record {pid}: {clean(s['Title'])}",
                     "authors": "NASA Physical Sciences Informatics (PSI)", "venue": "NASA PSI repository",
                     "year": None, "url": f"https://psi.nasa.gov/physci/repo/data/investigation/{pid}", "kind": "PSI"})
for e in NTRS_ONLY:
    out.append(e)

pathlib.Path("data/investigations.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

refs_path = pathlib.Path("data/references.json")
refs = [r for r in json.loads(refs_path.read_text(encoding="utf-8")) if r["kind"] != "PSI"]
refs_path.write_text(json.dumps(refs + psi_refs, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(out), "investigations;", len(refs), "base refs +", len(psi_refs), "PSI refs")
