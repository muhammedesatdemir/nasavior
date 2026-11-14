"""Design system: Deep Space Telemetry. Tokens, CSS, and small HTML components (no emoji, no gradients)."""
from __future__ import annotations

import html

import streamlit as st

TOKENS = {
    "bg": "#0B0F17", "panel": "#111827", "border": "#1F2937", "text": "#F3F4F6", "muted": "#9CA3AF",
    "blue": "#38BDF8", "safe": "#10B981", "flammable": "#EF4444", "caution": "#F59E0B", "pill_bg": "#1E293B",
}
MONO = "'JetBrains Mono','Fira Code',ui-monospace,Consolas,monospace"
SANS = "'Inter',-apple-system,'Segoe UI',sans-serif"
PLOT_CFG = {"displayModeBar": False}

# Short labels used in citation pills
REF_SHORT = {
    "REF-BASS2-POSTER": "BASS-II poster", "REF-OLSON2012": "Olson & Ferkul 2012", "REF-MARCUM2016": "Marcum 2016",
    "REF-FERKUL2026": "Ferkul 2026", "REF-LUCI2025": "LUCI 2025", "REF-SAFFIRE123": "Saffire I-III",
    "REF-SAFFIRE45": "Saffire IV-V", "REF-SAFFIRE6": "Saffire VI", "REF-ISSFLOW": "ISS Node 1 THC",
    "REF-EXPATM": "Exploration Atm.", "REF-CHALLENGE2026": "Challenge brief",
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root{{--bg:{TOKENS['bg']};--panel:{TOKENS['panel']};--bd:{TOKENS['border']};--tx:{TOKENS['text']};--mu:{TOKENS['muted']};
--blue:{TOKENS['blue']};--safe:{TOKENS['safe']};--hot:{TOKENS['flammable']};--cau:{TOKENS['caution']};}}
html,body,[class*="css"],.stApp{{font-family:{SANS};color:var(--tx)}}
.stApp{{background:var(--bg)}}
[data-testid="stHeader"]{{background:transparent}}
[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,[data-testid="stStatusWidget"]{{display:none!important;visibility:hidden}}
.block-container{{padding-top:1.5rem;padding-bottom:2rem;max-width:1560px}}
[data-testid="stSidebar"]{{background:var(--panel);border-right:1px solid var(--bd)}}
[data-testid="stSidebar"] .block-container{{padding-top:1.5rem}}
h1,h2,h3,h4{{font-family:{SANS};font-weight:600;letter-spacing:0;color:var(--tx)}}
h3{{font-size:1.05rem;text-transform:uppercase;letter-spacing:.06em;color:var(--mu);font-weight:600;
    border-bottom:1px solid var(--bd);padding-bottom:.4rem;margin-top:1.2rem}}
.mono,code{{font-family:{MONO};font-variant-numeric:tabular-nums}}
code{{background:{TOKENS['pill_bg']};color:var(--blue);border-radius:3px;padding:1px 5px}}

/* header bar */
.hdr{{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;background:var(--panel);
  border:1px solid var(--bd);border-radius:4px;padding:10px 14px;margin-bottom:14px}}
.hdr .t{{font-family:{MONO};font-size:.82rem;letter-spacing:.08em;color:var(--tx);font-weight:600}}
.hdr .t span{{color:var(--mu);font-weight:400}}
.tag{{display:inline-block;font-family:{MONO};font-size:.74rem;font-variant-numeric:tabular-nums;color:var(--blue);
  background:var(--bg);border:1px solid var(--bd);border-radius:3px;padding:3px 8px;margin-left:6px}}
.tag.k{{color:var(--mu)}}

/* kpi card */
.kpi{{background:var(--panel);border:1px solid var(--bd);border-left:3px solid var(--blue);border-radius:4px;
  padding:10px 14px;height:100%}}
.kpi.safe{{border-left-color:var(--safe)}}.kpi.hot{{border-left-color:var(--hot)}}.kpi.cau{{border-left-color:var(--cau)}}
.kpi .l{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--mu)}}
.kpi .v{{font-family:{MONO};font-size:24px;font-weight:500;font-variant-numeric:tabular-nums;margin:2px 0 4px}}
.kpi .r{{font-size:11px;color:var(--mu);font-family:{MONO}}}

/* panel / row cards */
.pn{{background:var(--panel);border:1px solid var(--bd);border-radius:4px;padding:10px 14px;margin-bottom:8px}}
.pn.hot{{border-left:3px solid var(--hot)}}.pn.safe{{border-left:3px solid var(--safe)}}
.pn.cau{{border-left:3px solid var(--cau)}}.pn.blue{{border-left:3px solid var(--blue)}}
.pn .h{{font-weight:600}}
.st{{font-family:{MONO};font-size:.72rem;letter-spacing:.04em;margin-left:8px;font-weight:600}}
.st.hot{{color:var(--hot)}}.st.safe{{color:var(--safe)}}.st.cau{{color:var(--cau)}}.st.mu{{color:var(--mu)}}
.sub{{color:var(--mu);font-size:.82rem}}

/* citation pill */
a.pill,span.pill{{display:inline-block;font-family:{MONO};font-size:.72rem;background:{TOKENS['pill_bg']};color:var(--blue)!important;
  border-radius:3px;padding:1px 7px;margin:1px 3px 1px 0;text-decoration:none;border:1px solid var(--bd)}}
a.pill:hover{{border-color:var(--blue)}}

/* notes */
.nt{{border:1px solid var(--bd);border-left:3px solid var(--cau);background:var(--panel);border-radius:4px;
  padding:8px 12px;margin:6px 0;font-size:.88rem}}
.nt b{{font-family:{MONO};font-size:.74rem;letter-spacing:.05em;color:var(--cau)}}
.nt.blue{{border-left-color:var(--blue)}}.nt.blue b{{color:var(--blue)}}

/* controls */
[data-baseweb="tab-list"]{{gap:0;border-bottom:1px solid var(--bd)}}
button[data-baseweb="tab"]{{font-family:{MONO};font-size:.78rem;letter-spacing:.05em;text-transform:uppercase;
  background:transparent;color:var(--mu);border-radius:0;padding:8px 16px}}
button[data-baseweb="tab"][aria-selected="true"]{{color:var(--blue)}}
[data-baseweb="tab-highlight"]{{background:var(--blue)!important;height:2px}}
.stButton>button,.stTextInput input{{border-radius:4px;border:1px solid var(--bd);background:var(--panel);color:var(--tx);
  font-family:{SANS}}}
.stButton>button:hover{{border-color:var(--blue);color:var(--blue)}}
[data-testid="stExpander"]{{border:1px solid var(--bd);border-radius:4px;background:var(--panel)}}
[data-testid="stDataFrame"]{{border:1px solid var(--bd);border-radius:4px}}
div[data-testid="stSlider"] label,div[data-testid="stRadio"] label p{{font-size:.84rem}}
.sbl{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--mu);margin:.2rem 0 .4rem}}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def esc(s: object) -> str:
    return html.escape(str(s))


def pill(ref_id: str, page: str, url: str | None = None) -> str:
    label = REF_SHORT.get(ref_id, ref_id.replace("REF-", ""))
    txt = esc(f"[Ref: {label}, {page}]")
    return f'<a class="pill" href="{esc(url)}" target="_blank">{txt}</a>' if url else f'<span class="pill">{txt}</span>'


def kpi(label: str, value: str, ref: str = "", tone: str = "") -> str:
    return (f'<div class="kpi {tone}"><div class="l">{esc(label)}</div><div class="v">{esc(value)}</div>'
            f'<div class="r">{esc(ref) if ref else "&nbsp;"}</div></div>')


def note(kind: str, text: str, tone: str = "") -> str:
    return f'<div class="nt {tone}"><b>[{esc(kind)}]</b> {esc(text)}</div>'


def header_bar(env_label: str, g: float, o2: float, pressure_kpa: float) -> str:
    psi = pressure_kpa / 6.894757
    tags = (f'<span class="tag k">ENV: {esc(env_label.upper())}</span><span class="tag">GRAVITY: {g:g}g</span>'
            f'<span class="tag">O2: {o2:.1f}%</span><span class="tag">PRESS: {psi:.1f} psi</span>')
    return (f'<div class="hdr"><div class="t">NASAVIOR <span>//</span> MICROGRAVITY COMBUSTION &amp; FIRE SAFETY ATLAS</div>'
            f'<div>{tags}</div></div>')
