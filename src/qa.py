"""Ask the Atlas: retrieval + deterministic, citation-bound answers.

No generative model is used. Every sentence returned is copied from a dataset record and carries
its reference id and page. If nothing relevant is found the answer says so.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd
from rank_bm25 import BM25Okapi

from .engine import G_LABEL, G_LEVELS, State, in_lunar_envelope, investigations, limit_table, measurements_df
from .models import load_references

STOP = set("the a an of in on at for to is are was were what which who how does do did with and or by it its be "
           "there any under from as that this these those about can i we you".split())
MIN_SCORE = 1.0


def _tok(s: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9\.]+", s.lower()) if w not in STOP and len(w) > 1]


@dataclass
class Passage:
    text: str
    ref_id: str
    page: str
    kind: str      # finding | objective | measurement | impact
    source_id: str


@lru_cache(maxsize=1)
def _corpus() -> tuple[list[Passage], BM25Okapi]:
    ps: list[Passage] = []
    for i in investigations():
        head = f"{i.name} ({i.acronym or i.inv_id})"
        ps.append(Passage(f"{head}. Objective: {i.objective[:600]}", f"REF-{i.inv_id}" if i.source == "PSI" else i.ref_ids[0],
                          "PSI record" if i.source == "PSI" else "Atlas entry", "objective", i.inv_id))
        for f in i.key_findings:
            ps.append(Passage(f"{head}: {f.text}", f.ref_id, f.page_or_figure, "finding", i.inv_id))
        if i.impact:
            ps.append(Passage(f"{head} impact: {i.impact[:500]}", f"REF-{i.inv_id}", "PSI record", "impact", i.inv_id))
    df = measurements_df()
    for _, m in df.iterrows():
        bits = [m["material"], f"g={m['g_level']}", m["platform"], m["outcome"]]
        if pd.notna(m["o2_mole_pct"]):
            bits.append(f"O2 {m['o2_mole_pct']}%")
        if pd.notna(m["pressure_kpa"]):
            bits.append(f"{m['pressure_kpa']} kPa")
        if pd.notna(m["flow_velocity_cm_s"]):
            bits.append(f"flow {m['flow_velocity_cm_s']} cm/s")
        if pd.notna(m["limiting_o2_pct"]):
            bits.append(f"limiting O2 {m['limiting_o2_pct']}% ({m['limit_definition']})")
        if pd.notna(m["spread_rate_mm_s"]):
            bits.append(f"spread {m['spread_rate_mm_s']} mm/s")
        gl = {0.0: "microgravity 0g iss", 0.16: "lunar moon 0.16g", 0.38: "martian mars 0.38g", 1.0: "earth 1g normal gravity"}[m["g_level"]]
        ps.append(Passage(", ".join(bits) + f". {m['note']}", m["ref_id"], m["page_or_figure"], "measurement",
                          m["meas_id"]))
        ps[-1].text += f" [{gl}]"
    bm = BM25Okapi([_tok(p.text) for p in ps])
    return ps, bm


def _ref_label(ref_id: str) -> str:
    r = {x.ref_id: x for x in load_references()}.get(ref_id)
    return f"{r.title} ({r.url})" if r else ref_id


GRAV_WORDS = {"mars": 0.38, "martian": 0.38, "moon": 0.16, "lunar": 0.16, "iss": 0.0, "microgravity": 0.0,
              "freefall": 0.0, "earth": 1.0, "1g": 1.0, "0g": 0.0}


def _gravity_in(q: str) -> float | None:
    m = re.search(r"(?<![\d.])(\d(?:\.\d+)?)\s*g\b", q.lower())
    if m and float(m.group(1)) in G_LEVELS:
        return float(m.group(1))
    for w in re.findall(r"[a-z0-9]+", q.lower()):
        if w in GRAV_WORDS:
            return GRAV_WORDS[w]
    return None


def _o2_in(q: str) -> float | None:
    m = re.search(r"(\d{2}(?:\.\d+)?)\s*%", q)
    return float(m.group(1)) if m else None


GENERIC = set("data experiment experiments record records result results level levels oxygen happened relevant "
              "studied study tested test tests burn burned burning flame spread material materials safe safest "
              "habitat base moon mars martian lunar microgravity gravity iss earth".split())


@lru_cache(maxsize=1)
def _vocab() -> frozenset[str]:
    ps, _ = _corpus()
    return frozenset(w for p in ps for w in _tok(p.text))


def _unmatched_terms(question: str) -> list[str]:
    """Content words that appear nowhere in the dataset (e.g. a material we have no record of)."""
    out = []
    for w in _tok(question):
        if len(w) < 4 or w in GENERIC or re.fullmatch(r"[\d.]+g?", w):
            continue
        if not any(v == w or v.startswith(w) or w.startswith(v) and len(v) >= 5 for v in _vocab()):
            out.append(w)
    return out


def answer(question: str, k: int = 5) -> dict:
    """Returns {'status': 'ok'|'no_data', 'summary': str, 'evidence': [Passage...], 'notes': [str]}."""
    ps, bm = _corpus()
    scores = bm.get_scores(_tok(question))
    order = sorted(range(len(ps)), key=lambda i: scores[i], reverse=True)
    g, o2 = _gravity_in(question), _o2_in(question)
    notes: list[str] = []

    def keep(p: Passage) -> bool:
        if p.kind != "measurement" or g is None:
            return True
        row = measurements_df().set_index("meas_id").loc[p.source_id]
        return row["g_level"] == g

    picked = [ps[i] for i in order if scores[i] >= MIN_SCORE and keep(ps[i])][:k]

    # Structured coverage answer for "is there data at <g> and <O2>" type questions
    if g is not None and o2 is not None:
        df = measurements_df()
        d = df[(df["g_level"] == g)]
        near = d[(d["o2_mole_pct"].sub(o2).abs() <= 2) | (d["limiting_o2_pct"].sub(o2).abs() <= 2)]
        if near.empty:
            amb = d["o2_mole_pct"].dropna()
            lims = d["limiting_o2_pct"].dropna()
            cov = []
            if len(amb):
                cov.append(f"ambient-test O2 {amb.min():g}-{amb.max():g} %")
            if len(lims):
                cov.append(f"limiting O2 {lims.min():g}-{lims.max():g} %")
            notes.append(f"No record at {G_LABEL[g]} within +/-2 O2 points of {o2:g} %. Dataset coverage at this gravity: "
                         + ("; ".join(cov) if cov else "none") + ".")
        else:
            notes.append(f"{len(near)} record(s) at {G_LABEL[g]} within +/-2 O2 points of {o2:g} %.")
    if g is not None and g in (0.16, 0.38):
        notes.append("Partial-gravity records in this dataset are drop-tower tests of about 5 s (Olson & Ferkul 2012, Table I). "
                     "PSI itself holds no partial-gravity combustion data.")

    missing = _unmatched_terms(question)
    if missing:
        notes.insert(0, "The dataset has no record mentioning: " + ", ".join(missing) +
                     ". Results below are the closest related records, not an answer about those terms.")
    if not picked:
        return {"status": "no_data", "summary": "No NASA record in the Nasavior dataset matches this question. "
                "Nothing was generated; try naming an experiment (e.g. Saffire, BASS-II), a material or a gravity level.",
                "evidence": [], "notes": notes}
    return {"status": "partial" if missing else "ok",
            "summary": f"{len(picked)} source-cited record(s) matched. Each statement below is copied from the cited record.",
            "evidence": picked, "notes": notes}


EXAMPLES = [
    "Is there data for cable insulation at 0.38 g and 26 % oxygen?",
    "What happened to silicone samples in microgravity?",
    "Which experiments studied Lunar gravity?",
    "What oxygen level did PMMA burn at in BASS-II?",
    "What happened to Nomex in Saffire-II?",
    "Which experiments are relevant to smoke detection?",
]
