"""Nasavior: source-cited dashboard for NASA microgravity combustion experiments.
Space Apps 2026 - Flame in Freefall. Run: streamlit run app.py"""
import pandas as pd
import streamlit as st

from src.engine import (G_LABEL, STATUS_TEXT, State, coverage_matrix, environments, gap_statements, gravity_margin,
                        investigations, material_margins, measurements_df, paired_comparison, relevance)
from src.models import load_references
from src.qa import EXAMPLES, answer
from src.ui import charts

st.set_page_config(page_title="Nasavior | Flame in Freefall", page_icon="🔥", layout="wide")

st.markdown("""
<style>
:root{--card:#141b2f;--line:#2a3350;--accent:#ff7a2f;--mut:#9aa3b8;--ok:#009E73;--warn:#F0E442;--bad:#D55E00}
.block-container{padding-top:1.4rem;max-width:1500px}
h1,h2,h3{letter-spacing:.2px}
.hero{background:linear-gradient(120deg,#141b2f 0%,#1c2540 60%,#2a1a14 100%);border:1px solid var(--line);
 border-radius:14px;padding:18px 22px;margin-bottom:10px}
.hero h1{margin:0;font-size:2rem}.hero p{margin:.3rem 0 0;color:var(--mut)}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.78rem;border:1px solid var(--line);margin-right:6px}
.b-env{background:#2a1a14;border-color:var(--accent);color:#ffb88a}
.b-a{background:#0d2a22;border-color:var(--ok);color:#7de0c0}
.b-w{background:#2e2a0e;border-color:var(--warn);color:#f0e442}
.b-g{background:#1d2234;color:var(--mut)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:10px}
.story{border-left:4px solid var(--accent)}
.src{color:var(--mut);font-size:.8rem}
.kpi{font-size:1.7rem;font-weight:700}
</style>""", unsafe_allow_html=True)

REFS = {r.ref_id: r for r in load_references()}
ENVS = environments()
INV = {i.inv_id: i for i in investigations()}


def cite(ref_id: str, page: str) -> str:
    r = REFS.get(ref_id)
    return f"[{ref_id}]({r.url}) · {page}" if r else f"{ref_id} · {page}"


# ------------------------------------------------------------------ sidebar: Mission Control
with st.sidebar:
    st.markdown("### 🛰 Mission Control")
    order = ["iss", "lunar", "mars", "rover", "earth"]
    env_id = st.radio("Target environment", order, format_func=lambda k: ENVS[k].label, key="env")
    env = ENVS[env_id]
    if st.session_state.get("_env_last") != env_id:      # presets fill the controls; user can then override
        st.session_state["o2"] = float(env.o2_pct)
        st.session_state["p"] = float(env.pressure_kpa)
        st.session_state["flow"] = 20.0
        st.session_state["_env_last"] = env_id
    o2 = st.slider("Oxygen (mole %)", 15.0, 40.0, step=0.5, key="o2")
    pressure = st.slider("Total pressure (kPa)", 40.0, 105.0, step=0.5, key="p")
    flow = st.slider("Air flow (cm/s)", 0.0, 60.0, step=1.0, key="flow",
                     help="Forced-flow speed. In partial gravity, buoyant flow also exists, so the meaning of this slider differs by environment.")
    st.caption(f"Gravity: **{G_LABEL.get(env.g_level, env.g_level)}** · preset basis: "
               + ", ".join(f"[{b.ref_id}]({REFS[b.ref_id].url}) {b.page}" for b in env.basis))
    if env.assumption:
        st.warning(f"Assumption: {env.assumption_note}")
    st.caption(f"Flow note: {env.flow_note}")
    st.divider()
    st.caption("Matching tolerances: O2 ±2 pts · pressure ±15 kPa · flow ±10 cm/s. Nothing is extrapolated.")

state = State(env.g_level, o2, pressure, flow)
df = measurements_df()

# ------------------------------------------------------------------ header
st.markdown(f"""<div class="hero"><h1>🔥 Nasavior</h1>
<p>Source-cited insights from NASA microgravity combustion experiments · NASA Space Apps 2026 · Flame in Freefall</p>
<p><span class="badge b-env">{env.label}</span>
<span class="badge b-a">{len(df)} cited measurements</span>
<span class="badge b-a">{len(INV)} experiments</span>
<span class="badge b-g">{len(REFS)} references</span>
<span class="badge b-w">no extrapolated values</span></p></div>""", unsafe_allow_html=True)

tabs = st.tabs(["Overview", "Flammability", "Investigation Atlas", "Lunar & Mars gap", "Ask the Atlas",
                "Earth benefits", "About & data"])

# ------------------------------------------------------------------ Overview
with tabs[0]:
    st.markdown("""<div class="card story"><b>Passing a fire test on Earth does not mean a material is safe in space.</b><br>
NASA screens spacecraft materials with a 1 g test (NASA-STD-6001 Test 1). The measurements below show materials that kept
burning at lower oxygen in reduced gravity, and materials that did not spread in 0 g at all. Both effects are in NASA's own data.</div>""",
                unsafe_allow_html=True)
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.subheader("Measured limits at your gravity level")
        mm = material_margins(state)
        if mm.empty:
            st.info(f"No oxygen-limit measurements exist at {G_LABEL.get(state.g, state.g)} in the dataset. "
                    "Nothing is estimated from other gravity levels.")
        else:
            for r in mm.itertuples():
                tone = {"burns": "b-w", "uncertain": "b-g", "extinguishes": "b-a"}[r.status]
                extra = f" · test pressure {r.pressure_kpa:g} kPa differs from your {state.pressure_kpa:g} kPa" if r.pressure_differs else ""
                st.markdown(f"""<div class="card"><b>{r.material}</b> <span class="badge {tone}">{STATUS_TEXT[r.status]}</span><br>
Your O2 {state.o2:g} % vs measured survive-limit {r.uloi:g} % (Δ {r.delta_to_uloi:+g}) and self-extinguish limit {r.moc:g} %{extra}<br>
<span class="src">{cite(r.ref_id, r.page_or_figure)}{' · reduced-g drop-tower criteria differ from 1 g (stated by source)' if r.reduced_g_criteria else ''}</span></div>""",
                            unsafe_allow_html=True)
    with c2:
        st.subheader("Most relevant experiments")
        rel = relevance(state)
        for r in rel.head(5).itertuples():
            st.markdown(f"""<div class="card"><b>{r.name}</b> <span class="badge b-g">relevance {r.score}</span><br>
<span class="src">{r.reasons}</span></div>""", unsafe_allow_html=True)
        st.caption("Relevance = how many source-cited records match your selection. It shows where to look, not how dangerous something is.")
    st.subheader("Oxygen margin of safety versus 1 g")
    st.caption("Olson & Ferkul 2012, Eq. 1: mean low-g limit minus mean 1 g limit. Negative = burns at lower O2 than the 1 g test suggests.")
    gm = pd.concat([gravity_margin(m) for m in ["Mylar G", "Ultem 1000", "Nomex HT90-40"]])
    gm["gravity"] = gm["g_level"].map(G_LABEL)
    st.dataframe(gm.pivot(index="material", columns="gravity", values="delta_o2"), use_container_width=True)
    st.caption("Source: " + cite("REF-OLSON2012", "Table I (p.6), Eq. 1 (p.6)"))

# ------------------------------------------------------------------ Flammability
with tabs[1]:
    st.plotly_chart(charts.limits_by_gravity(state), use_container_width=True)
    st.caption("Source: " + cite("REF-OLSON2012", "Table I (p.6)") +
               ". Mylar/Ultem tested at 70.3 kPa, Nomex at 101.3 kPa. Reduced-g criteria are for ~5 s drop tests; "
               "0 g tests used 30 cm/s concurrent flow.")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.o2_flow_map(state), use_container_width=True)
        st.caption("Each marker is one flight sample; hover for source and page. Sources: " +
                   cite("REF-SAFFIRE123", "Table I (p.29)") + "; " + cite("REF-SAFFIRE45", "Table 1 (p.3)") + "; " +
                   cite("REF-SAFFIRE6", "Table 1 (p.3)"))
    with c2:
        st.plotly_chart(charts.paired_spread(), use_container_width=True)
        st.caption("Source: " + cite("REF-SAFFIRE123", "Table I (p.29)"))
    p = paired_comparison()
    st.subheader("0 g versus 1 g, sample by sample")
    show = p[["sample", "material", "thickness_mm", "mode", "outcome_0g", "outcome_1g", "spread_0g_mm_s", "spread_1g_mm_s", "verdict"]]
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.markdown("**BASS-II (ISS, PMMA 1/4 in. rod):** steady spread at **13.6 % O2** in 0 g versus a 1 g blowoff limit of **16 %** "
                "(negative margin of 2.4 % O2). " + cite("REF-BASS2-POSTER", "p.18"))

# ------------------------------------------------------------------ Atlas
with tabs[2]:
    st.subheader("Investigation Atlas")
    st.caption("24 NASA PSI investigations (metadata copied from PSI) + 2 entries from NTRS papers that PSI does not hold.")
    f1, f2, f3 = st.columns([2, 1, 1])
    q = f1.text_input("Search name, objective or finding", placeholder="e.g. smoke, Saffire, PMMA, cool flame")
    themes = sorted({i.theme for i in INV.values()})
    th = f2.multiselect("Theme", themes, default=themes, format_func=lambda t: t.replace("_", " "))
    only_q = f3.checkbox("Only with cited findings", value=False)
    rows = []
    for i in INV.values():
        blob = (i.name + " " + (i.acronym or "") + " " + i.objective + " " + " ".join(f.text for f in i.key_findings)).lower()
        if i.theme not in th or (q and q.lower() not in blob) or (only_q and not i.key_findings):
            continue
        rows.append({"ID": i.inv_id, "Experiment": i.name, "Acronym": i.acronym, "Platform": i.platform,
                     "Hardware": i.hardware, "Theme": i.theme.replace("_", " "), "Equipment": i.equipment_theme,
                     "Cited findings": len(i.key_findings), "Records": int((df["inv_id"] == i.inv_id).sum())})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=300)
    st.caption(f"{len(rows)} of {len(INV)} shown")
    for i in [INV[r["ID"]] for r in rows]:
        with st.expander(f"{i.inv_id} · {i.name}"):
            st.markdown(f"**Objective (as published):** {i.objective}")
            meta = [x for x in [("Platform", i.platform), ("Hardware", i.hardware), ("O2 range", i.o2_range_pct),
                                ("Flow range", i.flow_range_cm_s)] if x[1]]
            st.markdown(" · ".join(f"**{k}:** {v}" for k, v in meta))
            if i.ranges_ref:
                st.caption(f"Ranges from: {i.ranges_ref}")
            if i.key_findings:
                st.markdown("**Cited findings**")
                for f in i.key_findings:
                    st.markdown(f"- {f.text}  \n  <span class='src'>{cite(f.ref_id, f.page_or_figure)}</span>", unsafe_allow_html=True)
            else:
                st.caption("No quantitative findings were extracted for this experiment; objective text is from PSI.")
            if i.psi_url:
                st.markdown(f"[Open in NASA PSI]({i.psi_url})")

# ------------------------------------------------------------------ Gap
with tabs[3]:
    st.subheader("Where NASA data is missing for the Moon and Mars")
    st.plotly_chart(charts.coverage_heatmap(), use_container_width=True)
    for s in gap_statements():
        st.markdown(f"- {s}")
    st.markdown("""<div class="card story"><b>Why this matters.</b> NASA reports that materials may burn at lower oxygen in partial gravity
than in 1 g, with flame spread rate peaking near Lunar gravity. NASA also plans FM2, the first combustion experiments on the Moon (launch planned late 2026).
<br><span class="src">""" + cite("REF-FERKUL2026", "p.1") + """</span></div>""", unsafe_allow_html=True)
    st.markdown("**Lunar atmosphere envelope used here:** O2 ≥ 30 %, pressure ≤ 10.2 psi (70.3 kPa), per the challenge brief and NASA's "
                "exploration-atmosphere design reference. " + cite("REF-EXPATM", "p.2"))

# ------------------------------------------------------------------ Ask
with tabs[4]:
    st.subheader("Ask the Atlas")
    st.caption("Search over the cited dataset. Answers are copied from records and carry their source; no text is generated. "
               "If nothing matches, it says so.")
    cols = st.columns(3)
    for n, ex in enumerate(EXAMPLES):
        if cols[n % 3].button(ex, key=f"ex{n}", use_container_width=True):
            st.session_state["qbox"] = ex
    question = st.text_input("Your question", key="qbox", placeholder="Type a question about NASA combustion experiments")
    if question:
        a = answer(question)
        tone = {"ok": "✅", "partial": "⚠️", "no_data": "⚪"}[a["status"]]
        st.markdown(f"**{tone} {a['summary']}**")
        for n in a["notes"]:
            st.warning(n)
        for p in a["evidence"]:
            st.markdown(f"""<div class="card">{p.text}<br><span class="src">{p.kind} · {cite(p.ref_id, p.page)}</span></div>""",
                        unsafe_allow_html=True)

# ------------------------------------------------------------------ Earth benefits
with tabs[5]:
    st.subheader("Earth benefits reported by NASA PSI")
    st.caption("Texts are copied from the 'Research Impacts / Earth Benefits' field of each PSI record.")
    for i in INV.values():
        if i.impact:
            with st.expander(i.name):
                st.write(i.impact)
                st.caption(f"Source: [PSI record {i.inv_id}]({i.psi_url})")

# ------------------------------------------------------------------ About
with tabs[6]:
    st.subheader("How Nasavior stays honest")
    st.markdown("""
- **Every number is transcribed from a NASA document** and shown with its reference and page or table.
- **No extrapolation:** a limit is shown only for the gravity level where it was measured.
- **No generated answers:** *Ask the Atlas* retrieves records; it never writes new facts.
- **Environment presets** list their basis; where sources do not define an environment (Mars habitat, rover) the UI says it is an assumption.

**Known limitations**
- Reduced-gravity limits (0.16 g, 0.38 g) come only from drop-tower tests (5.18 s) with criteria that differ from 1 g (stated by the source).
- Saffire I-III Table I gives no pressure; left empty.
- Saffire VI per-sample heat release / CO / CO2 columns were garbled in text extraction and are not used.
- PSI investigation links follow the PSI web-app route and were not browser-tested.
- Relevance ranking is a search aid, not a hazard score.
""")
    st.subheader("References")
    for r in REFS.values():
        if r.kind != "PSI":
            st.markdown(f"- **{r.ref_id}** · {r.authors}. *{r.title}*. {r.venue}. [{r.url}]({r.url})")
    st.caption("PSI records: " + ", ".join(f"[{i.inv_id}]({i.psi_url})" for i in INV.values() if i.psi_url))
