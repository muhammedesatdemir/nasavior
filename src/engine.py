"""Comparison engine. Pure functions over the frozen, source-cited datasets.

Principles
- Nothing is extrapolated: a limit is reported only for the gravity level it was measured at.
- Every result row carries ref_id + page_or_figure so the UI can always show the source.
- "No data" is a first-class result.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from .models import Environment, load_environments, load_investigations, load_measurements

G_LEVELS = [0.0, 0.16, 0.38, 1.0]
G_LABEL = {0.0: "0 g (microgravity)", 0.16: "0.16 g (Lunar)", 0.38: "0.38 g (Martian)", 1.0: "1 g (Earth)"}

# Tolerances used when matching a user state to measured test conditions (documented in the UI).
TOL_O2 = 2.0      # mole % points
TOL_P = 15.0      # kPa
TOL_FLOW = 10.0   # cm/s


@dataclass(frozen=True)
class State:
    g: float
    o2: float
    pressure_kpa: float
    flow_cm_s: float | None = None


def state_from_env(e: Environment, flow: float | None = None) -> State:
    return State(e.g_level, e.o2_pct, e.pressure_kpa, flow if flow is not None else e.flow_cm_s)


@lru_cache(maxsize=1)
def measurements_df() -> pd.DataFrame:
    df = pd.DataFrame([m.model_dump() for m in load_measurements()])
    df["g_label"] = df["g_level"].map(G_LABEL)
    return df


@lru_cache(maxsize=1)
def investigations() -> list:
    return load_investigations()


@lru_cache(maxsize=1)
def environments() -> dict:
    return {e.id: e for e in load_environments()}


# ---------------------------------------------------------------- limits / margin
def limit_table(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per (material, g, test pressure) pairing ULOI-type and MOC-type limits."""
    df = measurements_df() if df is None else df
    lim = df[df["outcome"] == "limit"].copy()
    lim["kind"] = lim["limit_definition"].map(
        {"ULOI": "uloi", "ULOI_dropstar": "uloi", "MOC": "moc", "MOC_dropstar": "moc"})
    paired = lim.dropna(subset=["kind"])
    out = []
    for (mat, g, p), grp in paired.groupby(["material", "g_level", "pressure_kpa"]):
        u = grp[grp["kind"] == "uloi"]
        m = grp[grp["kind"] == "moc"]
        if u.empty or m.empty:
            continue
        out.append({
            "material": mat, "g_level": g, "pressure_kpa": p,
            "uloi": float(u["limiting_o2_pct"].iloc[0]), "moc": float(m["limiting_o2_pct"].iloc[0]),
            "reduced_g_criteria": bool(u["limit_definition"].iloc[0].endswith("dropstar")),
            "flow_cm_s": u["flow_velocity_cm_s"].iloc[0], "ref_id": u["ref_id"].iloc[0],
            "page_or_figure": "Table I (p.6)",
        })
    return pd.DataFrame(out)


def margin_status(o2: float, uloi: float, moc: float) -> str:
    if o2 >= uloi:
        return "burns"        # at/above the O2 where the flame survived in the tests
    if o2 <= moc:
        return "extinguishes"  # at/below the O2 where the flame self-extinguished in the tests
    return "uncertain"


STATUS_TEXT = {
    "burns": "Flame survived at this O2 in the tests",
    "uncertain": "Between the tested self-extinguish and survive limits",
    "extinguishes": "Flame self-extinguished at this O2 in the tests",
}


def material_margins(state: State, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Compare the selected O2 with measured limits at the SAME gravity level. No extrapolation."""
    lt = limit_table(df)
    if lt.empty:
        return lt
    sel = lt[lt["g_level"] == state.g].copy()
    if sel.empty:
        return sel
    sel["status"] = [margin_status(state.o2, u, m) for u, m in zip(sel["uloi"], sel["moc"])]
    sel["delta_to_uloi"] = (state.o2 - sel["uloi"]).round(2)
    sel["pressure_differs"] = (sel["pressure_kpa"] - state.pressure_kpa).abs() > TOL_P
    return sel.sort_values("delta_to_uloi", ascending=False).reset_index(drop=True)


def gravity_margin(material: str, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Oxygen margin of safety vs 1g, as defined by Olson & Ferkul 2012 (Eq. 1): mean low-g limit - mean 1g limit."""
    lt = limit_table(df)
    one = lt[(lt["material"] == material) & (lt["g_level"] == 1.0)]
    if one.empty:
        return pd.DataFrame()
    base = (one["uloi"].iloc[0] + one["moc"].iloc[0]) / 2
    rows = []
    for _, r in lt[(lt["material"] == material) & (lt["g_level"] != 1.0)].iterrows():
        rows.append({"material": material, "g_level": r["g_level"],
                     "delta_o2": round((r["uloi"] + r["moc"]) / 2 - base, 2),
                     "ref_id": r["ref_id"], "page_or_figure": "Eq. 1 + Table I (p.6)"})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 0g vs 1g pairs
def paired_comparison(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Saffire I-III samples that have both a 0g flight and a 1g ground result."""
    df = measurements_df() if df is None else df
    d = df[df["meas_id"].str.startswith("M-SF123-")].copy()
    d["sample"] = d["meas_id"].str.extract(r"M-SF123-(\d-\d)-")
    z = d[d["g_level"] == 0.0].set_index("sample")
    o = d[d["g_level"] == 1.0].set_index("sample")
    rows = []
    for s in z.index.intersection(o.index):
        rows.append({
            "sample": s, "material": z.loc[s, "material"], "thickness_mm": z.loc[s, "thickness_mm"],
            "mode": z.loc[s, "spread_mode"], "outcome_0g": z.loc[s, "outcome"], "outcome_1g": o.loc[s, "outcome"],
            "spread_0g_mm_s": z.loc[s, "spread_rate_mm_s"], "spread_1g_mm_s": o.loc[s, "spread_rate_mm_s"],
            "ref_id": z.loc[s, "ref_id"], "page_or_figure": z.loc[s, "page_or_figure"],
        })
    out = pd.DataFrame(rows)

    def verdict(r):
        a, b = r["outcome_0g"], r["outcome_1g"]
        spread = ("burn", "partial")
        if a == "no_spread" and b == "no_spread":
            return "No spread in either"
        if a == "no_spread" and b in spread:
            return "Burned in 1g only"
        if a in spread and b == "no_spread":
            return "Burned in 0g only"
        if a == "anchored" and b in spread:
            return "0g: flame anchored; 1g: spread"
        if a in spread and b in spread:
            return "Spread in both"
        return "See outcomes"
    if not out.empty:
        out["verdict"] = out.apply(verdict, axis=1)
    return out


# ---------------------------------------------------------------- coverage / gaps
def in_lunar_envelope(df: pd.DataFrame) -> pd.Series:
    """Challenge-defined lunar atmosphere: O2 >= 30 % and pressure <= 70.3 kPa (10.2 psi)."""
    return (df["o2_mole_pct"] >= 30.0) & (df["pressure_kpa"] <= 70.3 + 0.05)


def coverage_matrix(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Counts of source-cited records per gravity level and condition class. Zeros are the data gaps."""
    df = measurements_df() if df is None else df
    rows = []
    for g in G_LEVELS:
        d = df[df["g_level"] == g]
        tested = d[d["o2_mole_pct"].notna()]
        rows.append({
            "g_level": g, "label": G_LABEL[g], "records": len(d),
            "limit_records": int((d["outcome"] == "limit").sum()),
            "with_pressure_le_70kPa": int((d["pressure_kpa"] <= 70.35).sum()),
            "ambient_o2_ge_30": int((tested["o2_mole_pct"] >= 30).sum()),
            "lunar_envelope_tests": int(in_lunar_envelope(d).sum()),
            "flight_platform_records": int((d["platform"].isin(["ISS", "Cygnus"])).sum()),
        })
    return pd.DataFrame(rows)


def gap_statements(df: pd.DataFrame | None = None) -> list[str]:
    cov = coverage_matrix(df).set_index("g_level")
    out = []
    for g in (0.16, 0.38):
        r = cov.loc[g]
        out.append(f"{G_LABEL[g]}: {int(r['records'])} source-cited records, all oxygen-limit results from "
                   f"5-second drop-tower tests; {int(r['lunar_envelope_tests'])} records with an ambient test "
                   f"condition inside the lunar atmosphere envelope (O2 >= 30 %, P <= 70.3 kPa).")
    z = cov.loc[0.0]
    out.append(f"{G_LABEL[0.0]}: {int(z['records'])} records; {int(z['lunar_envelope_tests'])} with an ambient test "
               f"condition inside the lunar atmosphere envelope (Saffire VI flights, which were in microgravity, not lunar gravity).")
    out.append("No record in this dataset measures flame spread in long-duration partial gravity "
               "(the FM2 lunar-surface experiment is planned; see Atlas entry NTRS-PARTIALG). "
               "This describes this dataset, not everything NASA may hold.")
    return out


def summary_points(state: State) -> list[tuple[str, list[tuple[str, str]]]]:
    """Deterministic, citation-bound summary of what the dataset says for the selected state.
    Each item: (sentence, [(ref_id, page), ...]). No generative text."""
    df = measurements_df()
    out: list[tuple[str, list[tuple[str, str]]]] = []
    mm = material_margins(state)
    if mm.empty:
        out.append((f"No oxygen-limit measurement exists at {G_LABEL.get(state.g, state.g)} in this dataset; "
                    "limits from other gravity levels are not substituted.", []))
    else:
        lims = ", ".join(f"{r.material} {r.uloi:g} %" for r in mm.itertuples())
        above = int((mm["status"] == "burns").sum())
        out.append((f"At {G_LABEL[state.g]} NASA measured survive-limits (lowest O2 at which the flame lasted) of {lims}. "
                    f"Your {state.o2:g} % O2 is at or above the survive-limit for {above} of {len(mm)} materials.",
                    [("REF-OLSON2012", "Table I, p.6")]))
    if state.g == 0.0:
        out.append(("BASS-II on the ISS sustained steady PMMA rod spread at 13.6 % O2 in microgravity, versus a 1 g blowoff "
                    "limit of 16 % O2.", [("REF-BASS2-POSTER", "p.18")]))
        out.append(("In Saffire-II, silicone samples of 0.27 to 1.03 mm did not spread in microgravity at 20 cm/s, although "
                    "the thinnest burned completely in 1 g: reduced gravity is not uniformly worse.",
                    [("REF-SAFFIRE123", "Table I, p.29")]))
    elif state.g in (0.16, 0.38):
        n = int((df["g_level"] == state.g).sum())
        out.append((f"This dataset holds {n} records at {state.g:g} g, all 5-second drop-tower limits; none describe "
                    "long-duration flame spread in this gravity.", [("REF-OLSON2012", "Table I, p.6")]))
        out.append(("NASA reports that some materials burn at lower oxygen in partial gravity than in 1 g, and plans FM2, the "
                    "first combustion experiments on the Moon.", [("REF-FERKUL2026", "p.1")]))
    else:
        out.append(("Earth (1 g) is the baseline of the NASA-STD-6001 Test 1 screen. In BASS-II the 1 g blowoff limit of the "
                    "PMMA rod was 16 % O2.", [("REF-BASS2-POSTER", "p.18")]))
    top = [r for r in relevance(state).head(3).itertuples() if r.score > 0]
    if top:
        out.append(("Experiments whose recorded conditions best match your selection: " + "; ".join(r.name for r in top) + ".", []))
    return out


# ---------------------------------------------------------------- relevance ranking
def relevance(state: State, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Rank investigations by how many of their source-cited records match the selected conditions.
    This is a relevance ranking (where to look), not a hazard score."""
    df = measurements_df() if df is None else df
    inv = {i.inv_id: i for i in investigations()}
    rows = []
    for inv_id, i in inv.items():
        d = df[df["inv_id"] == inv_id]
        if d.empty:
            rows.append({"inv_id": inv_id, "name": i.name, "score": 0, "reasons": "No quantitative records in dataset",
                         "records": 0, "theme": i.theme})
            continue
        gm = d["g_level"] == state.g
        o2m = d["o2_mole_pct"].sub(state.o2).abs() <= TOL_O2
        o2m = o2m | d["limiting_o2_pct"].sub(state.o2).abs().le(TOL_O2)
        pm = d["pressure_kpa"].sub(state.pressure_kpa).abs() <= TOL_P
        fm = pd.Series(False, index=d.index) if state.flow_cm_s is None else \
            d["flow_velocity_cm_s"].sub(state.flow_cm_s).abs() <= TOL_FLOW
        flight = bool((gm & d["platform"].isin(["ISS", "Cygnus"])).any())
        score = 3 * int(gm.any()) + 2 * int(o2m.any()) + 1 * int(pm.any()) + 1 * int(fm.any()) + int(flight)
        reasons = []
        if gm.any():
            reasons.append(f"{int(gm.sum())} record(s) at g = {state.g}")
        if o2m.any():
            reasons.append(f"O2 within +/-{TOL_O2:g} pts ({int(o2m.sum())})")
        if pm.any():
            reasons.append(f"pressure within +/-{TOL_P:g} kPa ({int(pm.sum())})")
        if fm.any():
            reasons.append(f"flow within +/-{TOL_FLOW:g} cm/s ({int(fm.sum())})")
        if flight:
            reasons.append("long-duration flight data")
        rows.append({"inv_id": inv_id, "name": i.name, "score": score,
                     "reasons": "; ".join(reasons) or "Records exist but none match the selected conditions",
                     "records": len(d), "theme": i.theme})
    return pd.DataFrame(rows).sort_values(["score", "records"], ascending=False).reset_index(drop=True)


def test_points(state: State, df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Measured test conditions (non-limit records with ambient O2 and flow) for the O2 x flow map."""
    df = measurements_df() if df is None else df
    return df[df["o2_mole_pct"].notna() & df["flow_velocity_cm_s"].notna() & (df["outcome"] != "limit")].copy()
