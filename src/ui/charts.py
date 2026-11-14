"""Plotly figures built only from source-cited measurements. Hover always shows ref_id and page."""
from __future__ import annotations

import plotly.graph_objects as go

from ..engine import G_LABEL, G_LEVELS, State, coverage_matrix, limit_table, measurements_df, paired_comparison

# Material hues are colour-blind safe and avoid the status colours (red = flammable, green = sub-limit).
C = {"orange": "#E69F00", "sky": "#56B4E9", "pink": "#CC79A7", "grey": "#9CA3AF", "blue": "#38BDF8",
     "hot": "#EF4444", "safe": "#10B981", "caution": "#F59E0B"}
MAT_COLOR = {"Mylar G": C["sky"], "Ultem 1000": C["orange"], "Nomex HT90-40": C["pink"], "PMMA": C["blue"]}
BG, PANEL, GRID, TXT = "rgba(0,0,0,0)", "#111827", "#1F2937", "#F3F4F6"
FONT = "JetBrains Mono, Fira Code, Consolas, monospace"


def _base(fig: go.Figure, title: str, height: int = 420, bottom: int = 90, left: int = 55) -> go.Figure:
    fig.update_layout(title=dict(text=title, x=0, font=dict(size=13, family=FONT, color=TXT)), height=height,
                      paper_bgcolor=BG, plot_bgcolor=PANEL, font=dict(color=TXT, size=11, family=FONT),
                      margin=dict(l=left, r=20, t=50, b=bottom), legend=dict(orientation="h", y=-0.3, font=dict(size=10)),
                      hoverlabel=dict(bgcolor="#0B0F17", bordercolor="#1F2937", font=dict(family=FONT, size=11)))
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, automargin=True)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, automargin=True)
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
        fig.add_trace(go.Scatter(x=d["g_level"], y=d["uloi"], mode="lines+markers", name=f"{mat} ULOI",
                                 line=dict(color=col, width=2), marker=dict(size=8), hovertext=hov, hoverinfo="text"))
        fig.add_trace(go.Scatter(x=d["g_level"], y=d["moc"], mode="lines+markers", name=f"{mat} MOC",
                                 line=dict(color=col, width=2, dash="dot"), marker=dict(size=8, symbol="diamond-open"),
                                 hovertext=hov, hoverinfo="text"))
    fig.add_hline(y=state.o2, line=dict(color=C["blue"], width=2, dash="dash"),
                  annotation_text=f"SELECTED O2 {state.o2:g}%", annotation_position="top left",
                  annotation_font=dict(color=C["blue"], family=FONT, size=11))
    fig.update_xaxes(title="Gravity level (g)", tickvals=G_LEVELS, ticktext=["0", "0.16", "0.38", "1"])
    fig.update_yaxes(title="Limiting O2 (mole %)")
    return _base(fig, "Limiting O2 by gravity level (measured)", 440)


def o2_flow_map(state: State) -> go.Figure:
    """Measured microgravity/1g test points in the O2 x flow plane, with the user's operating point."""
    df = measurements_df()
    d = df[df["o2_mole_pct"].notna() & df["flow_velocity_cm_s"].notna() & (df["outcome"] != "limit")]
    sym = {"burn": "circle", "anchored": "square", "partial": "triangle-up", "no_spread": "x", "no_ignition": "x"}
    col = {"burn": C["hot"], "anchored": C["caution"], "partial": C["sky"], "no_spread": C["grey"]}
    fig = go.Figure()
    for oc, grp in d.groupby("outcome"):
        hov = [f"{r.material}<br>{r.outcome}, {G_LABEL[r.g_level]}<br>O2 {r.o2_mole_pct:g} %, flow {r.flow_velocity_cm_s:g} cm/s"
               f"<br>{'P ' + format(r.pressure_kpa, 'g') + ' kPa' if r.pressure_kpa == r.pressure_kpa else 'P not stated'}"
               f"<br>{r.ref_id} {r.page_or_figure}" for r in grp.itertuples()]
        fig.add_trace(go.Scatter(x=grp["flow_velocity_cm_s"], y=grp["o2_mole_pct"], mode="markers", name=oc.replace("_", " "),
                                 marker=dict(size=11, symbol=sym.get(oc, "circle"), color=col.get(oc, C["grey"]),
                                             line=dict(width=1, color="#0B0F17")), hovertext=hov, hoverinfo="text"))
    fig.add_hline(y=state.o2, line=dict(color=C["blue"], width=1.5, dash="dash"),
                  annotation_text=f"O2 {state.o2:g}%", annotation_position="top left",
                  annotation_font=dict(color=C["blue"], family=FONT, size=10))
    if state.flow_cm_s is not None:
        fig.add_vline(x=state.flow_cm_s, line=dict(color=C["blue"], width=1.5, dash="dash"),
                      annotation_text=f"{state.flow_cm_s:g} cm/s", annotation_position="top right",
                      annotation_font=dict(color=C["blue"], family=FONT, size=10))
    fig.update_xaxes(title="Flow velocity (cm/s)", range=[0, 35])
    fig.update_yaxes(title="Ambient O2 (mole %)")
    return _base(fig, "Tested conditions: O2 x flow (0 g flights)", 420)


def paired_spread() -> go.Figure:
    p = paired_comparison()
    fig = go.Figure()
    short = lambda m: "SIBAL" if "SIBAL" in m else "Silicone" if "Silicone" in m else "PMMA" if "PMMA" in m else m.split()[0]
    labels = [f"{r.sample} {short(r.material)}" for r in p.itertuples()]
    hov0 = [f"{l}<br>0 g: {r.outcome_0g}<br>{r.ref_id} {r.page_or_figure}" for l, r in zip(labels, p.itertuples())]
    hov1 = [f"{l}<br>1 g: {r.outcome_1g}<br>{r.ref_id} {r.page_or_figure}" for l, r in zip(labels, p.itertuples())]
    fig.add_trace(go.Bar(x=labels, y=p["spread_0g_mm_s"].fillna(0), name="0 g flight", marker_color=C["sky"],
                         hovertext=hov0, hoverinfo="text"))
    fig.add_trace(go.Bar(x=labels, y=p["spread_1g_mm_s"].fillna(0), name="1 g ground", marker_color=C["orange"],
                         hovertext=hov1, hoverinfo="text"))
    fig.update_yaxes(title="Spread rate (mm/s)")
    fig.update_xaxes(tickangle=-40)
    return _base(fig, "0 g vs 1 g, same samples", 420, bottom=110)


def coverage_heatmap() -> go.Figure:
    cov = coverage_matrix()
    cols = [("records", "All records"), ("limit_records", "Limit (O2) records"), ("with_pressure_le_70kPa", "Pressure <= 10.2 psi"),
            ("ambient_o2_ge_30", "Ambient O2 >= 30 %"), ("lunar_envelope_tests", "Inside lunar envelope"),
            ("flight_platform_records", "ISS / Cygnus flights")]
    z = [[int(cov.loc[i, c]) for c, _ in cols] for i in cov.index]
    fig = go.Figure(go.Heatmap(z=z, x=[n for _, n in cols], y=list(cov["label"]), text=z, texttemplate="%{text}", textfont=dict(color="#F3F4F6", family=FONT, size=13),
                               colorscale=[[0, "#4A3410"], [0.001, "#12324A"], [1, "#1E6A94"]], showscale=False,
                               hovertemplate="%{y}<br>%{x}: %{z} record(s)<extra></extra>", xgap=3, ygap=3))
    fig.update_yaxes(autorange="reversed")
    return _base(fig, "Source-cited records by gravity and condition", 360, bottom=110, left=150)
