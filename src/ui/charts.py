"""Plotly figures built only from source-cited measurements. Hover always shows ref_id and page."""
from __future__ import annotations

import plotly.graph_objects as go

from ..engine import G_LABEL, G_LEVELS, State, coverage_matrix, limit_table, measurements_df, paired_comparison

# Okabe-Ito colour-blind-safe palette
C = {"orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442", "blue": "#0072B2",
     "verm": "#D55E00", "pink": "#CC79A7", "grey": "#9aa3b8"}
MAT_COLOR = {"Mylar G": C["sky"], "Ultem 1000": C["orange"], "Nomex HT90-40": C["green"], "PMMA": C["pink"]}
BG, PANEL, GRID, TXT = "rgba(0,0,0,0)", "#141b2f", "#2a3350", "#e6e9f2"


def _base(fig: go.Figure, title: str, height: int = 420) -> go.Figure:
    fig.update_layout(title=dict(text=title, x=0, font=dict(size=15)), height=height, paper_bgcolor=BG,
                      plot_bgcolor=PANEL, font=dict(color=TXT, size=12), margin=dict(l=50, r=20, t=55, b=50),
                      legend=dict(orientation="h", y=-0.22), hoverlabel=dict(bgcolor="#0b1020"))
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID)
    return fig


def limits_by_gravity(state: State) -> go.Figure:
    """Measured ULOI*/MOC* per material at each gravity level (Olson & Ferkul 2012 Table I) + chosen O2."""
    lt = limit_table()
    fig = go.Figure()
    for mat in ["Mylar G", "Ultem 1000", "Nomex HT90-40"]:
        d = lt[lt["material"] == mat].sort_values("g_level")
        col = MAT_COLOR[mat]
        hov = [f"{mat}<br>{G_LABEL[g]}<br>ULOI {u} %, MOC {m} %<br>test pressure {p:g} kPa<br>{r} {pg}"
               for g, u, m, p, r, pg in zip(d["g_level"], d["uloi"], d["moc"], d["pressure_kpa"], d["ref_id"],
                                            d["page_or_figure"])]
        fig.add_trace(go.Scatter(x=d["g_level"], y=d["uloi"], mode="lines+markers", name=f"{mat}: survives (ULOI)",
                                 line=dict(color=col, width=2), marker=dict(size=9), hovertext=hov, hoverinfo="text"))
        fig.add_trace(go.Scatter(x=d["g_level"], y=d["moc"], mode="lines+markers", name=f"{mat}: self-extinguishes (MOC)",
                                 line=dict(color=col, width=2, dash="dot"), marker=dict(size=8, symbol="diamond-open"),
                                 hovertext=hov, hoverinfo="text"))
    fig.add_hline(y=state.o2, line=dict(color=C["verm"], width=2), annotation_text=f"selected O2 {state.o2:g} %",
                  annotation_position="top left", annotation_font_color=C["verm"])
    fig.update_xaxes(title="Gravity level (g)", tickvals=G_LEVELS, ticktext=["0", "0.16", "0.38", "1"])
    fig.update_yaxes(title="Limiting O2 (mole %)")
    return _base(fig, "Limiting oxygen by gravity level (measured, drop-tower criteria for reduced g)", 440)


def o2_flow_map(state: State) -> go.Figure:
    """Measured microgravity/1g test points in the O2 x flow plane, with the user's operating point."""
    df = measurements_df()
    d = df[df["o2_mole_pct"].notna() & df["flow_velocity_cm_s"].notna() & (df["outcome"] != "limit")]
    sym = {"burn": "circle", "anchored": "square", "partial": "triangle-up", "no_spread": "x", "no_ignition": "x"}
    col = {"burn": C["orange"], "anchored": C["yellow"], "partial": C["sky"], "no_spread": C["grey"]}
    fig = go.Figure()
    for oc, grp in d.groupby("outcome"):
        hov = [f"{r.material}<br>{r.outcome}, {G_LABEL[r.g_level]}<br>O2 {r.o2_mole_pct:g} %, flow {r.flow_velocity_cm_s:g} cm/s"
               f"<br>{'P ' + format(r.pressure_kpa, 'g') + ' kPa' if r.pressure_kpa == r.pressure_kpa else 'P not stated'}"
               f"<br>{r.ref_id} {r.page_or_figure}" for r in grp.itertuples()]
        fig.add_trace(go.Scatter(x=grp["flow_velocity_cm_s"], y=grp["o2_mole_pct"], mode="markers", name=oc.replace("_", " "),
                                 marker=dict(size=12, symbol=sym.get(oc, "circle"), color=col.get(oc, C["grey"]),
                                             line=dict(width=1, color="#fff")), hovertext=hov, hoverinfo="text"))
    if state.flow_cm_s is not None:
        fig.add_trace(go.Scatter(x=[state.flow_cm_s], y=[state.o2], mode="markers", name="your selection",
                                 marker=dict(size=16, symbol="star", color=C["verm"], line=dict(width=1, color="#fff")),
                                 hovertext=[f"Selected: O2 {state.o2:g} %, flow {state.flow_cm_s:g} cm/s"], hoverinfo="text"))
    fig.update_xaxes(title="Flow velocity (cm/s)", range=[0, 35])
    fig.update_yaxes(title="Ambient O2 (mole %)")
    return _base(fig, "Where NASA has tested: ambient O2 x flow (Saffire I-VI; all ISS/Cygnus flights, 0 g)", 420)


def paired_spread() -> go.Figure:
    p = paired_comparison()
    fig = go.Figure()
    labels = [f"{r.sample} {r.material.split(' (')[0]} {r.thickness_mm if r.thickness_mm == r.thickness_mm else ''}mm".strip()
              for r in p.itertuples()]
    hov0 = [f"{l}<br>0 g: {r.outcome_0g}<br>{r.ref_id} {r.page_or_figure}" for l, r in zip(labels, p.itertuples())]
    hov1 = [f"{l}<br>1 g: {r.outcome_1g}<br>{r.ref_id} {r.page_or_figure}" for l, r in zip(labels, p.itertuples())]
    fig.add_trace(go.Bar(x=labels, y=p["spread_0g_mm_s"].fillna(0), name="0 g flight", marker_color=C["sky"],
                         hovertext=hov0, hoverinfo="text"))
    fig.add_trace(go.Bar(x=labels, y=p["spread_1g_mm_s"].fillna(0), name="1 g ground", marker_color=C["orange"],
                         hovertext=hov1, hoverinfo="text"))
    fig.update_yaxes(title="Spread rate (mm/s); 0 = no steady rate reported or no spread")
    fig.update_xaxes(tickangle=-30)
    return _base(fig, "Same samples, 0 g vs 1 g (Saffire I-III Table I). Silicone burned in 1 g but did not spread in 0 g", 430)


def coverage_heatmap() -> go.Figure:
    cov = coverage_matrix()
    cols = [("records", "All records"), ("limit_records", "Limit (O2) records"), ("with_pressure_le_70kPa", "Pressure <= 70 kPa"),
            ("ambient_o2_ge_30", "Ambient O2 >= 30 %"), ("lunar_envelope_tests", "Inside lunar envelope"),
            ("long_duration_gt_60s", "Long-duration (ISS/Cygnus)")]
    z = [[int(cov.loc[i, c]) for c, _ in cols] for i in cov.index]
    fig = go.Figure(go.Heatmap(z=z, x=[n for _, n in cols], y=list(cov["label"]), text=z, texttemplate="%{text}",
                               colorscale=[[0, "#3a1f1f"], [0.001, "#1b3a5c"], [1, "#56B4E9"]], showscale=False,
                               hovertemplate="%{y}<br>%{x}: %{z} record(s)<extra></extra>", xgap=3, ygap=3))
    fig.update_yaxes(autorange="reversed")
    return _base(fig, "Data coverage: number of source-cited records (0 = gap, shown dark red)", 340)
