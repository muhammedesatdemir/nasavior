"""Builds data/measurements.csv from values transcribed by hand from the cited NASA documents.
Every row carries ref_id + page_or_figure. Fields not stated in the source are left empty (null).
Run: python scripts/build_measurements.py"""
import csv
import pathlib

COLS = ["meas_id", "inv_id", "material", "thickness_mm", "geometry", "spread_mode", "g_level", "platform",
        "test_duration_s", "pressure_kpa", "o2_mole_pct", "flow_velocity_cm_s", "outcome", "spread_rate_mm_s",
        "flame_length_cm", "limiting_o2_pct", "limit_definition", "evidence_tier", "ref_id", "page_or_figure", "note"]
rows = []


def add(**kw):
    r = {c: "" for c in COLS}
    r.update(kw)
    rows.append(r)


PSI2KPA = 6.894757

# ---- Olson & Ferkul 2012, Table I (page 6): limiting O2 mole % ----
OF = "REF-OLSON2012"
mats = {  # material: (thickness mm = mil*0.0254, test pressure psia)
    "Mylar G": (0.127, 10.2), "Ultem 1000": (0.254, 10.2), "Nomex HT90-40": (0.305, 14.7)}
table = {  # (label, g, definition, platform): values for Mylar, Ultem, Nomex
    ("1g ULOI", 1.00, "ULOI", "ground_1g"): (21.2, 23.5, 23.5),
    ("1g MOC", 1.00, "MOC", "ground_1g"): (20.0, 23.0, 22.1),
    ("Martian ULOI*", 0.38, "ULOI_dropstar", "drop_tower"): (18.0, 22.0, 19.9),
    ("Martian MOC*", 0.38, "MOC_dropstar", "drop_tower"): (17.0, 21.1, 19.0),
    ("Lunar ULOI*", 0.16, "ULOI_dropstar", "drop_tower"): (15.6, 21.0, 21.0),
    ("Lunar MOC*", 0.16, "MOC_dropstar", "drop_tower"): (14.1, 19.9, 19.9),
    ("0g ULOI*", 0.00, "ULOI_dropstar", "drop_tower"): (17.0, 24.0, 23.0),
    ("0g MOC*", 0.00, "MOC_dropstar", "drop_tower"): (16.0, 23.0, 22.0),
}
n = 0
for (label, g, d, plat), vals in table.items():
    for (m, (th, psia)), v in zip(mats.items(), vals):
        n += 1
        note = ("Limiting O2 from Table I; reduced-g limits use drop-tower criteria (ULOI*/MOC*) that differ "
                "from 1g (source states this). Concurrent flow.")
        if g == 0.0:
            note += " 0g tests used concurrent forced flow of 30 cm/s."
        if g == 0.16:
            note += " Lunar-g values are carried from Ferkul & Olson 2011 as tabulated in this paper."
        add(meas_id=f"M-OF12-{n:03d}", inv_id="", material=m, thickness_mm=th,
            geometry="fabric" if m == "Nomex HT90-40" else "film", spread_mode="concurrent", g_level=g,
            platform=plat, test_duration_s=5.18 if plat == "drop_tower" else "",
            pressure_kpa=round(psia * PSI2KPA, 1), flow_velocity_cm_s=30 if g == 0.0 else "", outcome="limit",
            limiting_o2_pct=v, limit_definition=d, evidence_tier="A", ref_id=OF,
            page_or_figure=f"Table I (p.6): {label}", note=note)

# ---- BASS-II poster (NTRS 20160000593) p.18 ----
add(meas_id="M-BASS2-001", inv_id="PSI-25", material="PMMA", thickness_mm=6.35, geometry="rod",
    spread_mode="concurrent", g_level=0.0, platform="ISS", outcome="limit", limiting_o2_pct=13.6,
    limit_definition="lowest_burn_ug", evidence_tier="A", ref_id="REF-BASS2-POSTER", page_or_figure="p.18",
    note="1/4 in. PMMA rod, stagnation-point concurrent flow: steady spreading obtained at 13.6% O2. "
         "Flow speed and pressure for this point not stated in source.")
add(meas_id="M-BASS2-002", inv_id="PSI-25", material="PMMA", thickness_mm=6.35, geometry="rod",
    spread_mode="concurrent", g_level=1.0, platform="ground_1g", outcome="limit", limiting_o2_pct=16.0,
    limit_definition="blowoff_1g", evidence_tier="A", ref_id="REF-BASS2-POSTER", page_or_figure="p.18",
    note="1g blowoff limit for the 1/4 in. rod is 16% O2; source derives a negative oxygen margin of safety "
         "of 2.4% O2 versus BASS-II 0g.")

# ---- Saffire I-III (NTRS 20170008805) Table I (p.29) ----
SF = "REF-SAFFIRE123"
# id, inv, material, thickness, geometry, mode, o2, flow, outcome0g, spread0g, note0g, outcome1g, spread1g, note1g
S = [
    ("1-1", "PSI-98", "Cotton-fiberglass (SIBAL) fabric", 0.37, "fabric", "concurrent", 21.7, 20, "burn", 1.8,
     "40.6 cm x 94 cm sample; ~84 cm burned in 420 s; average flame power 1200 +/- 300 W (p.8, p.17).",
     "burn", "", "1g: complete burn, acceleratory (no steady spread rate)."),
    ("1-2", "PSI-98", "Cotton-fiberglass (SIBAL) fabric", 0.37, "fabric", "opposed", 21.5, 20, "burn", 1.3,
     "~10 cm burned in 70 s.", "no_spread", "", "1g: ~0 burn length."),
    ("2-1", "PSI-99", "Silicone sheet", 0.27, "thin_sheet", "concurrent", 22.1, 20, "no_spread", "",
     "Igniter-only damage; tiny gas-phase flame did not spread (p.12).", "burn", "",
     "1g: ~complete burn, acceleratory."),
    ("2-2", "PSI-99", "Silicone sheet", 0.61, "thin_sheet", "concurrent", 22.1, 20, "no_spread", "",
     "Did not spread (p.12).", "partial", 1.2, "1g: 7.6 cm burned."),
    ("2-3", "PSI-99", "Silicone sheet", 1.03, "thin_sheet", "concurrent", 22.1, 20, "no_spread", "",
     "Did not spread (p.12).", "no_spread", "", "1g: ~0 burn."),
    ("2-4", "PSI-99", "Silicone sheet", 0.37, "thin_sheet", "opposed", 22.1, 20, "no_spread", "",
     "Downward/opposed test; did not spread (p.12).", "burn", 0.6, "1g: complete burn."),
    ("2-5", "PSI-99", "Cotton-fiberglass (SIBAL) fabric", 0.37, "fabric", "concurrent", 22.1, 20, "burn", 2.1,
     "5 cm wide; 29 cm burned in 145 s.", "burn", "", "1g: complete burn, acceleratory."),
    ("2-6", "PSI-99", "Cotton-fiberglass (SIBAL) fabric", 0.37, "fabric", "concurrent", 22.1, 25, "burn", 2.6,
     "5 cm wide; 29 cm burned in 115 s.", "burn", "", "1g: complete burn, acceleratory."),
    ("2-8", "PSI-99", "PMMA slab (grooved)", "", "thick_slab", "concurrent", 22.1, 20, "anchored", "",
     "Flame anchored at sample base, very slow regression 0.01-0.04 mm/s (Table I note iv); flame length 8.0 cm "
     "per REF-SAFFIRE45 p.8.", "burn", "", "1g: complete burn, acceleratory."),
    ("2-9", "PSI-99", "PMMA slab (flat)", 10, "thick_slab", "concurrent", 22.0, 20, "anchored", "",
     "Flame anchored at sample base, very slow regression 0.01-0.04 mm/s (Table I note iv); flame length 9.5 cm "
     "per REF-SAFFIRE45 p.8.", "burn", "", "1g: complete burn, acceleratory."),
]
for (sid, inv, mat, th, geo, mode, o2, flow, o0, sp0, n0, o1, sp1, n1) in S:
    add(meas_id=f"M-SF123-{sid}-0G", inv_id=inv, material=mat, thickness_mm=th, geometry=geo, spread_mode=mode,
        g_level=0.0, platform="Cygnus", o2_mole_pct=o2, flow_velocity_cm_s=flow, outcome=o0, spread_rate_mm_s=sp0,
        evidence_tier="A", ref_id=SF, page_or_figure="Table I (p.29)",
        note=n0 + " Pressure not stated in source; ISS/Cygnus ambient air.")
    add(meas_id=f"M-SF123-{sid}-1G", inv_id=inv, material=mat, thickness_mm=th, geometry=geo, spread_mode=mode,
        g_level=1.0, platform="ground_1g", outcome=o1, spread_rate_mm_s=sp1, evidence_tier="A", ref_id=SF,
        page_or_figure="Table I (p.29)", note=n1)
add(meas_id="M-SF123-2-7-0G", inv_id="PSI-99", material="PMMA (5 cm) + Nomex HT90-40 composite",
    geometry="composite", spread_mode="concurrent", g_level=0.0, platform="Cygnus", o2_mole_pct=22.1,
    flow_velocity_cm_s=20, outcome="partial", evidence_tier="A", ref_id=SF, page_or_figure="Table I (p.29), p.24-25",
    note="0.85 mm PMMA section completely consumed; Nomex fabric (0.37 mm) was not ignited. "
         "Average PMMA flame power 460 +/- 50 W. 1g: Nomex ~0 burn.")

# ---- Saffire IV/V (NTRS 20210011521) Table 1 (p.3), Table 2 (p.8), text p.9 ----
S45 = "REF-SAFFIRE45"
add(meas_id="M-SF45-IV1", inv_id="", material="Cotton-fiberglass (SIBAL) fabric", geometry="fabric",
    spread_mode="concurrent", g_level=0.0, platform="Cygnus", pressure_kpa=100.0, o2_mole_pct=22.0,
    flow_velocity_cm_s=20, outcome="burn", flame_length_cm=8.5, evidence_tier="A", ref_id=S45,
    page_or_figure="Table 1 (p.3), Table 2 (p.8)",
    note="Steady-state flame size 8.5 cm (max 11.0 cm); duct height 30 cm; 41 cm wide, 50 cm long. "
         "Flight Saffire IV, sample 1.")
add(meas_id="M-SF45-IV2", inv_id="", material="PMMA (two-sided)", geometry="thick_slab", spread_mode="concurrent",
    g_level=0.0, platform="Cygnus", pressure_kpa=100.0, o2_mole_pct=22.0, flow_velocity_cm_s=20,
    outcome="anchored", flame_length_cm=9.5, evidence_tier="A", ref_id=S45, page_or_figure="Table 1 (p.3), p.8-9",
    note="Did not spread appreciably; flame stayed at leading edge; flame grew to 9.5 cm after 400 s then "
         "reached a limiting length. 18 cm sample. Flight Saffire IV, sample 2.")
add(meas_id="M-SF45-V2", inv_id="", material="Cotton jersey", geometry="fabric", spread_mode="concurrent",
    g_level=0.0, platform="Cygnus", pressure_kpa=70.7, o2_mole_pct=26.2, flow_velocity_cm_s=20, outcome="burn",
    flame_length_cm=10.0, evidence_tier="A", ref_id=S45, page_or_figure="Table 1 (p.3), Table 2 (p.8)",
    note="Steady-state flame size 10.0 cm (max 14.0 cm); duct height 30 cm. Exploration-like atmosphere. "
         "Flight Saffire V, sample 2.")
add(meas_id="M-SF45-V3", inv_id="", material="PMMA (one-sided)", geometry="thick_slab", spread_mode="concurrent",
    g_level=0.0, platform="Cygnus", pressure_kpa=71.3, o2_mole_pct=25.4, flow_velocity_cm_s=20,
    outcome="anchored", flame_length_cm=11.0, evidence_tier="A", ref_id=S45, page_or_figure="Table 1 (p.3), p.9",
    note="Did not spread appreciably; flame grew to 11 cm after 450 s then reached a limiting length. "
         "Flight Saffire V, sample 3.")
add(meas_id="M-SF45-V4", inv_id="", material="Structured PMMA", geometry="thick_slab", spread_mode="opposed",
    g_level=0.0, platform="Cygnus", pressure_kpa=72.6, o2_mole_pct=25.7, flow_velocity_cm_s=20, outcome="burn",
    evidence_tier="A", ref_id=S45, page_or_figure="Table 1 (p.3)",
    note="Opposed flow, 20 cm sample with ribs. Ignition included a deflagration (p.7). Flight Saffire V, sample 4.")

# ---- Saffire VI (NTRS 20240002981) Table 1 (p.3) ----
S6 = "REF-SAFFIRE6"
for sid, mat, geo, p, o2 in [("VI2", "Cotton-fiberglass (SIBAL) fabric", "fabric", 54.1, 31.0),
                             ("VI3", "PMMA (two-sided)", "thick_slab", 54.6, 30.3),
                             ("VI4", "PMMA (one-sided)", "thick_slab", 55.2, 28.8)]:
    add(meas_id=f"M-SF6-{sid}", inv_id="", material=mat, geometry=geo, spread_mode="concurrent", g_level=0.0,
        platform="Cygnus", pressure_kpa=p, o2_mole_pct=o2, flow_velocity_cm_s=20, outcome="burn",
        evidence_tier="A", ref_id=S6, page_or_figure="Table 1 (p.3)",
        note="Saffire VI, 41 cm wide samples. Source reports fire heat release of 1.5-3.2 kW across Saffire VI "
             "tests (per-sample values not transcribed).")

out = pathlib.Path("data/measurements.csv")
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows ->", out)
