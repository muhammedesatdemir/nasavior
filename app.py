"""Nasavior: source-cited atlas of NASA microgravity combustion experiments.
Space Apps 2026 - Flame in Freefall. Run: streamlit run app.py"""
import pandas as pd
import streamlit as st

from src.engine import (G_LABEL, STATUS_TEXT, State, coverage_matrix, environments, gap_statements, gravity_margin,
                        investigations, material_margins, measurements_df, paired_comparison, relevance)
from src.models import load_references
from src.qa import EXAMPLES, answer
from src.ui import charts
from src.ui.theme import PLOT_CFG, REF_SHORT, esc, header_bar, inject_css, kpi, note, pill

st.set_page_config(page_title="Nasavior | Flame in Freefall", page_icon=None, layout="wide",
                   initial_sidebar_state="expanded")
inject_css()

REFS = {r.ref_id: r for r in load_references()}
ENVS = environments()
INV = {i.inv_id: i for i in investigations()}
SHORT = {"iss": "ISS (0 g)", "lunar": "Lunar Base (0.16 g)", "mars": "Martian Habitat (0.38 g)",
         "rover": "Pressurized Rover", "earth": "Earth Baseline (1 g)"}
HDR = {"iss": "ISS", "lunar": "Lunar Base", "mars": "Martian Habitat", "rover": "Pressurized Rover",
       "earth": "Earth Baseline"}
STATUS_UI = {"burns": ("hot", "[FLAMMABLE IN TESTS]"), "uncertain": ("cau", "[UNCERTAIN]"),
             "extinguishes": ("safe", "[SUB-LIMIT]")}


def cite(ref_id: str, page: str) -> str:
    r = REFS.get(ref_id)
    return pill(ref_id, page, r.url if r else None)


def mono(x: object) -> str:
    return f'<span class="mono">{esc(x)}</span>'


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown('<div class="sbl">Mission control</div>', unsafe_allow_html=True)
    order = ["iss", "lunar", "mars", "rover", "earth"]
    env_id = st.radio("Target environment", order, format_func=lambda k: SHORT[k], key="env")
    env = ENVS[env_id]
    if st.session_state.get("_env_last") != env_id:  # presets fill the controls; the user can then override
        st.session_state["o2"] = float(env.o2_pct)
        st.session_state["p"] = float(env.pressure_kpa)
        st.session_state["flow"] = 20.0
        st.session_state["_env_last"] = env_id
    o2 = st.slider("Oxygen (mole %)", 15.0, 40.0, step=0.5, key="o2")
    pressure = st.slider("Total pressure (kPa)", 40.0, 105.0, step=0.5, key="p")
    flow = st.slider("Air flow (cm/s)", 0.0, 60.0, step=1.0, key="flow",
                     help="Forced-flow speed. In partial gravity buoyant flow also exists, so the meaning of this slider differs by environment.")
    st.markdown('<div class="sbl" style="margin-top:1rem">Preset basis</div>', unsafe_allow_html=True)
    st.markdown("".join(cite(b.ref_id, b.page) for b in env.basis), unsafe_allow_html=True)
    if env.assumption:
        st.markdown(note("ASSUMPTION", env.assumption_note), unsafe_allow_html=True)
    st.markdown(f'<div class="sub" style="margin-top:.6rem">Flow note: {esc(env.flow_note)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub" style="margin-top:.8rem">Match tolerance: O2 ±2 pts, pressure ±15 kPa, '
                'flow ±10 cm/s. Nothing is extrapolated.</div>', unsafe_allow_html=True)

state = State(env.g_level, o2, pressure, flow)
df = measurements_df()
st.markdown(header_bar(HDR[env_id], state.g, state.o2, state.pressure_kpa), unsafe_allow_html=True)

tabs = st.tabs(["Overview", "Flammability", "Investigation Atlas", "Lunar & Mars gap", "Ask the Atlas",
                "Earth benefits", "About & data"])

# ------------------------------------------------------------------ Overview
with tabs[0]:
    mm = material_margins(state)
    at_g = df[df["g_level"] == state.g]
    n_hot = int((mm["status"] == "burns").sum()) if not mm.empty else 0
    k = st.columns(4)
    k[0].markdown(kpi("Selected oxygen", f"{state.o2:.1f} %", f"{state.pressure_kpa / 6.894757:.1f} psi total"), unsafe_allow_html=True)
    if mm.empty:
        k[1].markdown(kpi("Materials above survive-limit", "NO DATA", "no limits at this g", "cau"), unsafe_allow_html=True)
    else:
        k[1].markdown(kpi("Materials above survive-limit", f"{n_hot} / {len(mm)}", "Olson & Ferkul 2012, Table I",
                          "hot" if n_hot else "safe"), unsafe_allow_html=True)
    k[2].markdown(kpi(f"Cited records at {state.g:g} g", str(len(at_g)), f"of {len(df)} total", "" if len(at_g) else "cau"),
                  unsafe_allow_html=True)
    lun = coverage_matrix().set_index("g_level").loc[state.g, "lunar_envelope_tests"]
    k[3].markdown(kpi("Tests in lunar envelope", str(int(lun)), "O2 >= 30 %, P <= 10.2 psi", "" if lun else "cau"),
                  unsafe_allow_html=True)

    st.markdown('<div class="pn blue" style="margin-top:12px"><span class="h">Passing a fire test on Earth does not mean '
                'a material is safe in space.</span><div class="sub">NASA screens spacecraft materials with a 1 g test '
                '(NASA-STD-6001 Test 1). The measurements here show materials that kept burning at lower oxygen in '
                'reduced gravity, and materials that did not spread in 0 g at all.</div></div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.markdown("### Measured limits at the selected gravity")
        if mm.empty:
            st.markdown(note("NO DATA", f"No oxygen-limit measurements exist at {G_LABEL.get(state.g, state.g)} in the "
                                       "dataset. Nothing is estimated from other gravity levels."), unsafe_allow_html=True)
        for r in mm.itertuples():
            tone, label = STATUS_UI[r.status]
            diff = (f'<div class="sub">Test pressure {mono(f"{r.pressure_kpa:g} kPa")} differs from your '
                    f'{mono(f"{state.pressure_kpa:g} kPa")}.</div>') if r.pressure_differs else ""
            crit = '<div class="sub">Reduced-g drop-tower criteria differ from 1 g (stated by source).</div>' if r.reduced_g_criteria else ""
            st.markdown(
                f'<div class="pn {tone}"><span class="h">{esc(r.material)}</span><span class="st {tone}">{label}</span>'
                f'<div class="sub">{esc(STATUS_TEXT[r.status])}. Your O2 {mono(f"{state.o2:g}%")} vs survive-limit '
                f'{mono(f"{r.uloi:g}%")} (delta {mono(f"{r.delta_to_uloi:+g}")}) and self-extinguish limit {mono(f"{r.moc:g}%")}.</div>'
                f'{diff}{crit}<div style="margin-top:4px">{cite(r.ref_id, r.page_or_figure)}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown("### Most relevant experiments")
        rel = relevance(state)
        for r in rel.head(5).itertuples():
            st.markdown(f'<div class="pn"><span class="h">{esc(r.name)}</span><span class="st mu">SCORE {r.score}</span>'
                        f'<div class="sub">{esc(r.reasons)}</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="sub">Relevance counts source-cited records that match your selection. It shows where to look, '
                    'not how dangerous something is.</div>', unsafe_allow_html=True)

    st.markdown("### Oxygen margin of safety versus 1 g")
    gm = pd.concat([gravity_margin(m) for m in ["Mylar G", "Ultem 1000", "Nomex HT90-40"]])
    gm["gravity"] = gm["g_level"].map(G_LABEL)
    tbl = gm.pivot(index="material", columns="gravity", values="delta_o2")
    st.dataframe(tbl, use_container_width=True)
    st.markdown('<div class="sub">Mean low-g limit minus mean 1 g limit (Eq. 1). Negative: burns at lower O2 than the 1 g test '
                'suggests.</div>' + cite("REF-OLSON2012", "Table I + Eq. 1, p.6"), unsafe_allow_html=True)

# ------------------------------------------------------------------ Flammability
with tabs[1]:
    st.plotly_chart(charts.limits_by_gravity(state), use_container_width=True, config=PLOT_CFG)
    st.markdown(cite("REF-OLSON2012", "Table I, p.6") + '<span class="sub"> Mylar and Ultem tested at 70.3 kPa, Nomex at 101.3 kPa. '
                'Reduced-g criteria are for 5 s drop tests; 0 g tests used 30 cm/s concurrent flow.</span>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(charts.o2_flow_map(state), use_container_width=True, config=PLOT_CFG)
        st.markdown(cite("REF-SAFFIRE123", "Table I, p.29") + cite("REF-SAFFIRE45", "Table 1, p.3") +
                    cite("REF-SAFFIRE6", "Table 1, p.3"), unsafe_allow_html=True)
    with c2:
        st.plotly_chart(charts.paired_spread(), use_container_width=True, config=PLOT_CFG)
        st.markdown(cite("REF-SAFFIRE123", "Table I, p.29"), unsafe_allow_html=True)
    st.markdown("### 0 g versus 1 g, sample by sample")
    p = paired_comparison()
    show = p[["sample", "material", "thickness_mm", "mode", "outcome_0g", "outcome_1g", "spread_0g_mm_s", "spread_1g_mm_s", "verdict"]].copy()
    show["source"] = "[Ref: Saffire I-III, Table I p.29]"
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.markdown('<div class="pn safe"><span class="h">BASS-II, PMMA 1/4 in. rod on the ISS</span>'
                f'<div class="sub">Steady spread at {mono("13.6% O2")} in 0 g versus a 1 g blowoff limit of {mono("16% O2")}: '
                f'negative margin of {mono("2.4% O2")}.</div>' + cite("REF-BASS2-POSTER", "p.18") + '</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ Atlas
with tabs[2]:
    st.markdown("### Investigation Atlas")
    st.markdown('<div class="sub">24 NASA PSI investigations (metadata copied from PSI) and 2 entries from NTRS papers that '
                'PSI does not hold.</div>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns([2, 1.2, 1])
    q = f1.text_input("Search name, objective or finding", placeholder="smoke, Saffire, PMMA, cool flame")
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
    st.markdown(f'<div class="sub">{len(rows)} of {len(INV)} shown</div>', unsafe_allow_html=True)
    for i in [INV[r["ID"]] for r in rows]:
        with st.expander(f"{i.inv_id}  |  {i.name}"):
            st.markdown(f"**Objective (as published):** {i.objective}")
            meta = [x for x in [("Platform", i.platform), ("Hardware", i.hardware), ("O2 range", i.o2_range_pct),
                                ("Flow range", i.flow_range_cm_s)] if x[1]]
            if meta:
                st.markdown(" | ".join(f"**{k}:** {v}" for k, v in meta))
            if i.ranges_ref:
                st.markdown(f'<span class="sub">Ranges from {esc(i.ranges_ref)}</span>', unsafe_allow_html=True)
            if i.key_findings:
                st.markdown("**Cited findings**")
                for f in i.key_findings:
                    st.markdown(f'<div class="pn blue">{esc(f.text)}<div style="margin-top:4px">{cite(f.ref_id, f.page_or_figure)}</div></div>',
                                unsafe_allow_html=True)
            else:
                st.markdown(note("NOTE", "No quantitative findings were extracted for this experiment; the objective is the PSI text."),
                            unsafe_allow_html=True)
            if i.psi_url:
                st.markdown(f'<a class="pill" href="{esc(i.psi_url)}" target="_blank">[Open in NASA PSI]</a>', unsafe_allow_html=True)

# ------------------------------------------------------------------ Gap
with tabs[3]:
    st.markdown("### Where NASA data is missing for the Moon and Mars")
    st.plotly_chart(charts.coverage_heatmap(), use_container_width=True, config=PLOT_CFG)
    for s in gap_statements():
        st.markdown(f'<div class="nt"><b>[GAP]</b> {esc(s)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="pn blue" style="margin-top:10px"><span class="h">Why this matters</span><div class="sub">NASA reports '
                'that materials may burn at lower oxygen in partial gravity than in 1 g, with flame spread rate peaking near '
                'Lunar gravity. NASA also plans FM2, the first combustion experiments on the Moon (launch planned late 2026).'
                '</div>' + cite("REF-FERKUL2026", "p.1") + '</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub" style="margin-top:8px">Lunar atmosphere envelope used here: O2 >= 30%, pressure <= 10.2 psi '
                '(70.3 kPa), per the challenge brief and the NASA exploration-atmosphere design reference.</div>' +
                cite("REF-EXPATM", "p.2"), unsafe_allow_html=True)

# ------------------------------------------------------------------ Ask
with tabs[4]:
    st.markdown("### Ask the Atlas")
    st.markdown('<div class="sub">Search over the cited dataset. Answers are copied from records and carry their source; '
                'no text is generated. If nothing matches, it says so.</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for n, ex in enumerate(EXAMPLES):
        if cols[n % 3].button(ex, key=f"ex{n}", use_container_width=True):
            st.session_state["qbox"] = ex
    question = st.text_input("Question", key="qbox", placeholder="Ask about a NASA combustion experiment, material or gravity level")
    if question:
        a = answer(question)
        tag = {"ok": ("safe", "[MATCH]"), "partial": ("cau", "[PARTIAL]"), "no_data": ("cau", "[NO DATA]")}[a["status"]]
        st.markdown(f'<div class="pn {tag[0]}"><span class="st {tag[0]}" style="margin-left:0">{tag[1]}</span> {esc(a["summary"])}</div>',
                    unsafe_allow_html=True)
        for n in a["notes"]:
            st.markdown(note("NOTE", n), unsafe_allow_html=True)
        for p in a["evidence"]:
            st.markdown(f'<div class="pn"><div class="sub mono" style="text-transform:uppercase">{esc(p.kind)}</div>'
                        f'{esc(p.text)}<div style="margin-top:4px">{cite(p.ref_id, p.page)}</div></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ Earth benefits
with tabs[5]:
    st.markdown("### Earth benefits reported by NASA PSI")
    st.markdown('<div class="sub">Texts are copied from the "Research Impacts / Earth Benefits" field of each PSI record.</div>',
                unsafe_allow_html=True)
    for i in INV.values():
        if i.impact:
            with st.expander(i.name):
                st.write(i.impact)
                st.markdown(pill(f"REF-{i.inv_id}", "PSI record", i.psi_url), unsafe_allow_html=True)

# ------------------------------------------------------------------ About
with tabs[6]:
    st.markdown("### How Nasavior stays honest")
    st.markdown("""
- **Every number is transcribed from a NASA document** and shown with its reference and page or table.
- **No extrapolation:** a limit is shown only for the gravity level where it was measured.
- **No generated answers:** Ask the Atlas retrieves records; it never writes new facts.
- **Environment presets list their basis;** where sources do not define an environment (Mars habitat, rover) the interface says it is an assumption.
""")
    st.markdown("### Known limitations")
    st.markdown("""
- Reduced-gravity limits (0.16 g, 0.38 g) come only from drop-tower tests (5.18 s) with criteria that differ from 1 g (stated by the source).
- Saffire I-III Table I gives no pressure; left empty.
- Saffire VI per-sample heat release, CO and CO2 columns were garbled in text extraction and are not used.
- PSI investigation links follow the PSI web-app route and were not browser-tested.
- Relevance ranking is a search aid, not a hazard score.
""")
    st.markdown("### References")
    for r in REFS.values():
        if r.kind != "PSI":
            st.markdown(f'<div class="pn">{pill(r.ref_id, "full record", r.url)} {esc(r.authors)}. <i>{esc(r.title)}</i>. {esc(r.venue)}.</div>',
                        unsafe_allow_html=True)
    st.markdown('<div class="sub">PSI records: ' + " ".join(pill(f"REF-{i.inv_id}", i.inv_id, i.psi_url) for i in INV.values() if i.psi_url) +
                "</div>", unsafe_allow_html=True)
