"""Builds the Space Apps demo deck (exactly 7 slides, 16:9) from one content definition.

Outputs
  docs/slides/nasavior_deck.html            1920x1080 HTML deck (source of the PDF)
  docs/Nasavior_SpaceApps2026_Slides.pdf    7-page PDF rendered by Chromium (Playwright)
  docs/Nasavior_SpaceApps2026_Slides.pptx   editable PowerPoint / Google Slides version

Run (repo root):  python scripts/build_slides.py
Needs: playwright (+ chromium), python-pptx.  See requirements-dev.txt.

Rules enforced here: exactly 7 slides, no NASA logo, design tokens of the app, no emoji,
every number below is taken from data/ (see PROVENANCE.md).
"""
from __future__ import annotations

import html
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SHOTS = DOCS / "screenshots"
HTML_OUT = DOCS / "slides" / "nasavior_deck.html"
PDF_OUT = DOCS / "Nasavior_SpaceApps2026_Slides.pdf"
PPTX_OUT = DOCS / "Nasavior_SpaceApps2026_Slides.pptx"

C = {"bg": "#0B0F17", "panel": "#111827", "line": "#1F2937", "text": "#F3F4F6", "mute": "#9CA3AF",
     "blue": "#38BDF8", "hot": "#EF4444", "amber": "#F59E0B", "safe": "#10B981", "pill": "#1E293B"}
TONE = {"blue": C["blue"], "hot": C["hot"], "amber": C["amber"], "safe": C["safe"], "mute": C["line"]}

LIVE = "https://nasavior.streamlit.app"
REPO = "https://github.com/muhammedesatdemir/nasavior"

# ------------------------------------------------------------------------------------------ content
# card: (tone, label, [paragraphs], [refs])        ref text is shown as [Ref: <text>]
S2 = [
    ("hot", "THE PHYSICS TRAP",
     ["NASA screens materials with a 1 g upward-burning test (NASA-STD-6001 Test 1).",
      "In low gravity buoyancy disappears. A slow ventilation flow can keep a flame alive, so some materials "
      "burn at lower oxygen than on Earth."],
     ["Ferkul 2026, p.1"]),
    ("amber", "THE DATA BOTTLENECK",
     ["Flight and drop-tower results are scattered across NASA PSI records and NTRS papers.",
      "No single place lets an engineer compare them for a target atmosphere, such as 34 % O2 at 8.2 psi."],
     ["Exploration Atm., p.2"]),
]
S3 = [
    ("blue", "SUMMARIZE", ["Condenses 26 experiments and 55 cited measurements into a summary for the chosen environment."], []),
    ("blue", "RANK", ["Orders experiments by how close their recorded gravity, O2, pressure and flow are to yours."], []),
    ("blue", "INTERPRET", ["Compares your O2 level with limits NASA measured at the same gravity, and shows where data is missing."], []),
]
S4 = [
    ("safe", "BASS-II  |  ISS, 0 g",
     ["PMMA rod kept burning at 13.6 % O2. The 1 g blowoff limit is 16.0 %."], ["BASS-II poster, p.18"]),
    ("blue", "DROP TOWER  |  0.16 g",
     ["Mylar G survived down to 15.6 % O2 at Lunar gravity (5 s drop). Its 1 g limit is 21.2 %."],
     ["Olson & Ferkul 2012, Table I"]),
    ("amber", "SAFFIRE-II  |  NOT ALWAYS WORSE",
     ["No silicone sample spread in 0 g at 22.1 % O2. The 0.27 mm sample burned completely in 1 g."],
     ["Saffire I-III, Table I"]),
]
S5 = [
    ("amber", "5.18 s",
     ["Every 0.16 g and 0.38 g limit in the Atlas comes from a drop-tower test this short."], ["Olson & Ferkul 2012, Table I"]),
    ("hot", "0",
     ["records at partial gravity inside the lunar atmosphere envelope (O2 ≥ 30 %, ≤ 10.2 psi). "
      "The 2 records inside it are Saffire VI flights in 0 g."], ["Saffire VI, Table 1"]),
]
S5_NOTE = "This describes the Nasavior dataset, not everything NASA holds."
S6 = [
    ("blue", "CITATION-BOUND SEARCH",
     ["Every answer is copied from a record and carries its [Ref: source, page]."], []),
    ("blue", "NO EXTRAPOLATION ACROSS GRAVITY",
     ["A 0 g result is never turned into a 0.16 g value."], []),
    ("amber", "EXPLICIT GUARDRAILS",
     ["Ask for a term the Atlas lacks and it says so: “The dataset has no record mentioning: cable, insulation.”"], []),
    ("safe", "NO AI MODEL AT RUN TIME",
     ["No API key, no generated text. Known limitations are listed in the app."], []),
]
S7_EARTH = ["Cleaner, more efficient combustion (PSI records ACME Flame Design, FLEX-2).",
            "Models for fire detection and suppression systems in space and on Earth."]
S7_EARTH_REFS = ["PSI-10, PSI-68", "BASS-II poster, p.5"]
S7_NEXT = ["FM2, NASA's planned first combustion tests on the Moon (launch planned late 2026), can be added as new rows."]
S7_NEXT_REFS = ["Ferkul 2026, p.1"]
TEAM = [("Muhammed Esat Demir", "Software & Product Lead"), ("Kevser Demir", "Data & Science Lead")]
AI_NOTE = "Code written with AI coding assistance. No AI model runs inside the app."

SLIDES = [  # (nav label, title, subtitle)
    ("01 THESIS", "NASAVIOR", "Microgravity Combustion & Fire Safety Atlas"),
    ("02 PROBLEM", "Why 1 g screening is not enough in space", None),
    ("03 SOLUTION", "Summarize. Rank. Interpret.", None),
    ("04 EVIDENCE", "What NASA actually measured", None),
    ("05 KEY FINDING", "The Lunar & Mars qualification gap", None),
    ("06 ARCHITECTURE", "Zero invented answers", None),
    ("07 IMPACT & LINKS", "Earth benefits, next steps, links", None),
]
IMAGES = {3: "01-overview-iss.png", 4: "02-flammability.png", 5: "04-lunar-mars-gap.png", 6: "05-ask-the-atlas.png"}
CROP = ROOT / "docs" / "slides" / "img"          # screenshots without the sidebar, generated here
SIDEBAR_PX = 300                                  # sidebar width in the 1440 px wide screenshots


def cropped(fname: str) -> Path:
    from PIL import Image
    CROP.mkdir(parents=True, exist_ok=True)
    out = CROP / fname
    im = Image.open(SHOTS / fname)
    im.crop((SIDEBAR_PX, 0, im.width, im.height)).save(out, optimize=True)
    return out
METRICS = [("26", "EXPERIMENTS IN THE ATLAS (24 NASA PSI)"), ("55", "PAGE-CITED MEASUREMENTS"),
           ("0", "EXTRAPOLATED VALUES OR GENERATED ANSWERS")]
THESIS = "Passing a fire test on Earth does not mean a material is safe in space."
KICKER = "NASA SPACE APPS CHALLENGE 2026 // FLAME IN FREEFALL"

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️]")


_NB = re.compile(r"(\d) (%|g\b|psi\b|s\b|mm\b|cm/s)|([≤≥]) (?=\d)")


def nb(s: str) -> str:
    """Keep a number and its unit on one line (no-break space)."""
    return _NB.sub(lambda m: (m.group(1) + " " + m.group(2)) if m.group(1) else (m.group(3) + " "), s)


def esc(s: str) -> str:
    return html.escape(nb(s), quote=True)


# ------------------------------------------------------------------------------------------ HTML
def pills(refs: list[str]) -> str:
    return "".join(f'<span class="pill">[Ref: {esc(r)}]</span>' for r in refs)


def card(tone: str, label: str, paras: list[str], refs: list[str], big: bool = False) -> str:
    body = "".join(f"<p>{esc(p)}</p>" for p in paras)
    lab = f'<div class="stat">{esc(label)}</div>' if big else f'<div class="lab">{esc(label)}</div>'
    return (f'<div class="card" style="border-left-color:{TONE[tone]}">{lab}{body}'
            f'<div class="refs">{pills(refs)}</div></div>')


def header(i: int) -> str:
    return (f'<div class="top"><span>NASAVIOR // {esc(SLIDES[i - 1][0])}</span><span>{i:02d} / 07</span></div>')


def title_block(i: int) -> str:
    return f'<h2>{esc(SLIDES[i - 1][1])}</h2>'


def two_col(i: int, cards_html: str, extra: str = "") -> str:
    img = IMAGES[i]
    return (f'{header(i)}{title_block(i)}<div class="cols"><div class="left">{cards_html}{extra}</div>'
            f'<div class="right"><img src="img/{img}" alt="Nasavior screenshot"></div></div>')


def slide_html() -> list[str]:
    out = []
    # 1
    metrics = "".join(f'<div class="metric"><div class="mv">{esc(v)}</div><div class="ml">{esc(l)}</div></div>' for v, l in METRICS)
    out.append(f'''{header(1)}<div class="kicker">{esc(KICKER)}</div><h1>NASAVIOR</h1>
<div class="sub">Microgravity Combustion &amp; Fire Safety Atlas</div>
<div class="thesis">{esc(THESIS)}</div><div class="metrics">{metrics}</div>
<div class="links"><div><span class="lab">LIVE APP</span> {esc(LIVE)}</div><div><span class="lab">REPOSITORY</span> {esc(REPO)}</div></div>''')
    # 2
    out.append(f'{header(2)}{title_block(2)}<div class="pair">{"".join(card(*c) for c in S2)}</div>'
               f'<div class="strip">A material that passes on Earth can still burn in orbit at lower oxygen.</div>')
    # 3..6
    out.append(two_col(3, "".join(card(*c) for c in S3)))
    out.append(two_col(4, "".join(card(*c) for c in S4)))
    out.append(two_col(5, "".join(card(*c, big=True) for c in S5), f'<div class="note">{esc(S5_NOTE)}</div>'))
    out.append(two_col(6, "".join(card(*c) for c in S6)))
    # 7
    team = "".join(f'<div class="person"><b>{esc(n)}</b><span>{esc(r)}</span></div>' for n, r in TEAM)
    out.append(f'''{header(7)}{title_block(7)}<div class="cols7"><div class="left7">
{card("safe", "EARTH SPINOFFS, AS STATED BY NASA", S7_EARTH, S7_EARTH_REFS)}
{card("amber", "NEXT STEPS", S7_NEXT, S7_NEXT_REFS)}</div>
<div class="right7"><div class="card" style="border-left-color:{C["blue"]}"><div class="lab">PROJECT LINKS &amp; TEAM</div>
<div class="kv"><span class="lab">LIVE APP</span><div class="url">{esc(LIVE)}</div></div>
<div class="kv"><span class="lab">REPOSITORY</span><div class="url">{esc(REPO)}</div></div>
<div class="kv"><span class="lab">DATA SOURCES</span><div class="src">NASA PSI and NASA NTRS (public NASA documents)</div></div>
<div class="kv"><span class="lab">TEAM</span>{team}</div>
<div class="ai">{esc(AI_NOTE)}</div></div></div></div>''')
    return out


CSS = f"""
@page {{ size: 1920px 1080px; margin: 0 }}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{C['bg']};color:{C['text']};font-family:'Inter','Segoe UI',Arial,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.slide{{position:relative;width:1920px;height:1080px;overflow:hidden;background:{C['bg']};padding:56px 88px 56px;break-after:page;page-break-after:always}}
.slide:last-child{{break-after:auto;page-break-after:auto}}
@media screen{{.slide{{margin:0 auto 24px}}}}
.mono,.top,.kicker,.lab,.pill,.stat,.ml,.mv,.url{{font-family:'JetBrains Mono','Consolas','Courier New',monospace;font-variant-numeric:tabular-nums}}
.top{{display:flex;justify-content:space-between;font-size:22px;letter-spacing:.08em;color:{C['mute']};border-bottom:1px solid {C['line']};padding-bottom:16px;margin-bottom:34px}}
h1{{font-size:168px;line-height:1;letter-spacing:.02em;font-weight:700;margin:18px 0 6px}}
h2{{font-size:62px;line-height:1.1;font-weight:700;margin-bottom:34px}}
.kicker{{font-size:26px;letter-spacing:.1em;color:{C['blue']};background:{C['panel']};border:1px solid {C['line']};border-radius:4px;display:inline-block;padding:10px 18px;margin-top:6px}}
.sub{{font-size:46px;color:{C['mute']};margin-bottom:40px}}
.thesis{{font-size:64px;line-height:1.18;font-weight:600;border-left:10px solid {C['blue']};background:{C['panel']};padding:30px 40px;border-radius:4px;margin-bottom:38px;max-width:1500px}}
.metrics{{display:flex;gap:24px;margin-bottom:34px}}
.metric{{flex:1;background:{C['panel']};border:1px solid {C['line']};border-radius:4px;padding:22px 28px}}
.mv{{font-size:78px;font-weight:600;color:{C['text']};line-height:1}}
.ml{{font-size:21px;letter-spacing:.06em;color:{C['mute']};margin-top:10px}}
.links{{font-family:'JetBrains Mono','Consolas',monospace;font-size:27px;color:{C['text']};display:flex;gap:56px}}
.links .lab{{color:{C['mute']};font-size:20px;letter-spacing:.08em;margin-right:10px}}
.card{{background:{C['panel']};border:1px solid {C['line']};border-left:8px solid {C['blue']};border-radius:4px;padding:22px 30px;margin-bottom:20px}}
.card p{{font-size:32px;line-height:1.32;margin-top:8px}}
.lab{{font-size:22px;letter-spacing:.09em;color:{C['mute']}}}
.stat{{font-size:84px;font-weight:600;line-height:1}}
.refs{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}
.refs:empty{{display:none}}
.pill{{background:{C['pill']};color:{C['blue']};font-size:20px;padding:4px 12px;border-radius:4px;border:1px solid {C['line']};white-space:nowrap}}
.pair{{display:flex;gap:28px;margin-bottom:26px}}
.pair .card{{flex:1;padding:44px 46px}}
.pair .card p{{font-size:44px;line-height:1.3;margin-top:20px}}
.strip{{margin-top:34px;font-size:50px;font-weight:600;color:{C['text']};border-top:1px solid {C['line']};padding-top:26px}}
.cols{{display:flex;gap:40px;align-items:flex-start}}
.left{{width:42%}}
.right{{width:58%;background:{C['panel']};border:1px solid {C['line']};border-radius:4px;padding:10px;display:flex;justify-content:center}}
.right img{{max-width:100%;max-height:770px;display:block;border-radius:2px}}
.note{{font-size:24px;color:{C['mute']};margin-top:6px}}
.cols7{{display:flex;gap:40px;align-items:stretch}}
.left7{{width:52%}}.right7{{width:48%;display:flex}}.right7 .card{{flex:1;margin-bottom:0}}
.cols7 .card p{{font-size:36px}}
.left7 .card:last-child{{margin-bottom:0}}
.kv{{margin-top:30px}}
.url{{font-size:25px;color:{C['text']};margin-top:6px;overflow-wrap:anywhere}}
.src{{font-size:30px;margin-top:6px}}
.person{{margin-top:12px;font-size:32px}}
.person b{{font-weight:600}}.person span{{color:{C['mute']};margin-left:14px;font-size:24px}}
.ai{{font-size:24px;color:{C['mute']};margin-top:34px;border-top:1px solid {C['line']};padding-top:14px}}
"""


def build_html() -> str:
    slides = "\n".join(f'<section class="slide" id="s{i}">{s}</section>' for i, s in enumerate(slide_html(), 1))
    doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Nasavior - Space Apps 2026</title>'
           f'<link rel="preconnect" href="https://fonts.googleapis.com">'
           f'<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">'
           f'<style>{CSS}</style></head><body>{slides}</body></html>')
    assert not EMOJI.search(doc), "emoji found in deck"
    assert "nasa logo" not in doc.lower()
    return doc


def build_pdf() -> int:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.goto(HTML_OUT.resolve().as_uri(), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(1500)
        n = pg.evaluate("document.querySelectorAll('.slide').length")
        overflow = pg.evaluate("""() => [...document.querySelectorAll('.slide')].map((s, i) => {
            const r = s.getBoundingClientRect(); let worst = 0;
            s.querySelectorAll('*').forEach(e => { const b = e.getBoundingClientRect();
                worst = Math.max(worst, b.bottom - r.bottom, b.right - r.right); });
            return [i + 1, Math.round(worst)]; })""")
        bad = [x for x in overflow if x[1] > 0]
        pg.pdf(path=str(PDF_OUT), width="1920px", height="1080px", print_background=True,
               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}, prefer_css_page_size=True)
        b.close()
    if bad:
        print("WARNING content exceeds slide bounds (slide, px):", bad)
    return n


# ------------------------------------------------------------------------------------------ PPTX
def rgb(h: str):
    from pptx.dml.color import RGBColor
    return RGBColor.from_string(h.lstrip("#").upper())


PX = 13.333 / 1920   # inches per px; 1 px of the 1920 design = 0.5 pt of type
SANS, MONO = "Arial", "Courier New"


def est_h(text: str, size_px: float, width_px: float, mono: bool = False, lh: float = 1.32) -> float:
    cw = size_px * (0.62 if mono else 0.52)
    per = max(1, int(width_px / cw))
    lines = 0
    for para in text.split("\n"):
        lines += max(1, math.ceil(len(para) / per))
    return lines * size_px * lh


def build_pptx() -> int:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Emu, Inches, Pt

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    warnings: list[str] = []

    def I(px: float):
        return Inches(px * PX)

    def rect(sl, x, y, w, h, fill, line=None, stripe=None):
        s = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, I(x), I(y), I(w), I(h))
        s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
        if line:
            s.line.color.rgb = rgb(line); s.line.width = Pt(0.75)
        else:
            s.line.fill.background()
        s.shadow.inherit = False
        if stripe:
            r2 = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, I(x), I(y), I(8), I(h))
            r2.fill.solid(); r2.fill.fore_color.rgb = rgb(stripe); r2.line.fill.background(); r2.shadow.inherit = False
        return s

    def text(sl, x, y, w, h, runs, size_px, color, mono=False, bold=False, anchor=MSO_ANCHOR.TOP, align=PP_ALIGN.LEFT):
        tb = sl.shapes.add_textbox(I(x), I(y), I(w), I(h))
        tf = tb.text_frame; tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = anchor
        first = True
        for para in runs if isinstance(runs, list) else [runs]:
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.alignment = align
            r = p.add_run(); r.text = nb(para)
            r.font.size = Pt(size_px * 0.5); r.font.bold = bold
            r.font.name = MONO if mono else SANS
            r.font.color.rgb = rgb(color)
        need = sum(est_h(t, size_px, w, mono) for t in (runs if isinstance(runs, list) else [runs]))
        if need > h + 2:
            warnings.append(f"text may overflow: {str(runs)[:50]!r} needs {need:.0f}px > {h:.0f}px")
        return tb

    def pill(sl, x, y, label):
        w = len(f"[Ref: {label}]") * 20 * 0.62 + 24
        rect(sl, x, y, w, 34, C["pill"], C["line"])
        text(sl, x + 12, y + 4, w - 20, 28, f"[Ref: {label}]", 20, C["blue"], mono=True)
        return w

    def refs_row(sl, x, y, maxw, refs):
        cx, cy = x, y
        for r in refs:
            w = len(f"[Ref: {r}]") * 20 * 0.62 + 24
            if cx + w > x + maxw:
                cx, cy = x, cy + 42
            pill(sl, cx, cy, r); cx += w + 8
        return cy + 34

    def bg(sl, i):
        sl.background.fill.solid(); sl.background.fill.fore_color.rgb = rgb(C["bg"])
        text(sl, 88, 56, 900, 30, f"NASAVIOR // {SLIDES[i - 1][0]}", 22, C["mute"], mono=True)
        text(sl, 1500, 56, 332, 30, f"{i:02d} / 07", 22, C["mute"], mono=True, align=PP_ALIGN.RIGHT)
        ln = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, I(88), I(98), I(1744), I(1)); ln.fill.solid()
        ln.fill.fore_color.rgb = rgb(C["line"]); ln.line.fill.background(); ln.shadow.inherit = False

    def title(sl, i):
        text(sl, 88, 128, 1744, 80, SLIDES[i - 1][1], 62, C["text"], bold=True)

    def stack_cards(sl, cards, x, y, w, big=False, body_px=32, max_y=1020):
        cy = y
        for tone, label, paras, refs in cards:
            inner = w - 8 - 60
            lab_h = 104 if big else 30
            body_h = sum(est_h(p, body_px, inner) + 8 for p in paras)
            n_ref_rows = 1 if not refs else math.ceil(sum(len(f"[Ref: {r}]") * 12.4 + 32 for r in refs) / inner)
            h = 22 + lab_h + 8 + body_h + (12 + n_ref_rows * 42 if refs else 0) + 22
            rect(sl, x, cy, w, h, C["panel"], C["line"], stripe=TONE[tone])
            text(sl, x + 38, cy + 22, inner, lab_h, label, 84 if big else 22, C["text"] if big else C["mute"], mono=True, bold=big)
            ty = cy + 22 + lab_h + 8
            for p in paras:
                ph = est_h(p, body_px, inner)
                text(sl, x + 38, ty, inner, ph + 4, p, body_px, C["text"]); ty += ph + 8
            if refs:
                refs_row(sl, x + 38, ty + 12, inner, refs)
            cy += h + 20
        if cy > max_y:
            warnings.append(f"cards end at {cy:.0f}px > {max_y}px")
        return cy

    def picture(sl, fname, x, y, w, h):
        from PIL import Image
        path = CROP / fname
        im = Image.open(path); iw, ih = im.size
        rect(sl, x, y, w, h, C["panel"], C["line"])
        scale = min((w - 20) / iw, (h - 20) / ih)
        pw, ph = iw * scale, ih * scale
        sl.shapes.add_picture(str(path), I(x + (w - pw) / 2), I(y + (h - ph) / 2), I(pw), I(ph))

    # 1
    s = prs.slides.add_slide(blank); bg(s, 1)
    rect(s, 88, 128, 1000, 52, C["panel"], C["line"])
    text(s, 106, 140, 970, 34, KICKER, 26, C["blue"], mono=True)
    text(s, 88, 185, 1744, 215, "NASAVIOR", 168, C["text"], bold=True)
    text(s, 88, 385, 1744, 64, "Microgravity Combustion & Fire Safety Atlas", 46, C["mute"])
    rect(s, 88, 480, 1500, 170, C["panel"], C["line"], stripe=C["blue"])
    text(s, 138, 495, 1420, 160, THESIS, 64, C["text"], bold=True)
    for k, (v, l) in enumerate(METRICS):
        x = 88 + k * (568 + 24)
        rect(s, x, 690, 568, 170, C["panel"], C["line"])
        text(s, x + 28, 700, 520, 100, v, 78, C["text"], mono=True, bold=True)
        text(s, x + 28, 805, 520, 56, l, 21, C["mute"], mono=True)
    text(s, 88, 905, 900, 40, f"LIVE APP  {LIVE}", 27, C["text"], mono=True)
    text(s, 88, 955, 1500, 40, f"REPOSITORY  {REPO}", 27, C["text"], mono=True)
    # 2
    s = prs.slides.add_slide(blank); bg(s, 2); title(s, 2)
    for k, (tone, label, paras, refs) in enumerate(S2):
        x = 88 + k * (860 + 24); w = 860
        body = sum(est_h(p, 38, w - 76) + 16 for p in paras)
        h = 34 + 30 + body + 80 + 34
        rect(s, x, 250, w, h, C["panel"], C["line"], stripe=TONE[tone])
        text(s, x + 38, 284, w - 76, 30, label, 22, C["mute"], mono=True)
        ty = 330
        for p in paras:
            ph = est_h(p, 38, w - 76); text(s, x + 38, ty + 16, w - 76, ph + 4, p, 38, C["text"]); ty += ph + 16
        refs_row(s, x + 38, ty + 40, w - 76, refs)
        if 250 + h > 900:
            warnings.append(f"slide 2 card too tall: {250 + h:.0f}")
    text(s, 88, 910, 1744, 70, "A material that passes on Earth can still burn in orbit at lower oxygen.", 44, C["text"], bold=True)
    # 3-6
    for i, cards, big, bpx in [(3, S3, False, 32), (4, S4, False, 28), (5, S5, True, 30), (6, S6, False, 26)]:
        s = prs.slides.add_slide(blank); bg(s, i); title(s, i)
        end = stack_cards(s, cards, 88, 240, 710, big=big, body_px=bpx)
        if i == 5:
            text(s, 88, end + 4, 710, 80, S5_NOTE, 24, C["mute"])
        picture(s, IMAGES[i], 838, 240, 994, 740)
    # 7
    s = prs.slides.add_slide(blank); bg(s, 7); title(s, 7)
    stack_cards(s, [("safe", "EARTH SPINOFFS, AS STATED BY NASA", S7_EARTH, S7_EARTH_REFS),
                    ("amber", "NEXT STEPS", S7_NEXT, S7_NEXT_REFS)], 88, 240, 900, body_px=30)
    x, w = 1028, 804
    rect(s, x, 240, w, 740, C["panel"], C["line"], stripe=C["blue"])
    yy = 262
    text(s, x + 38, yy, w - 76, 30, "PROJECT LINKS & TEAM", 22, C["mute"], mono=True); yy += 56
    for lab, val, mono_ in [("LIVE APP", LIVE, True), ("REPOSITORY", REPO, True),
                            ("DATA SOURCES", "NASA PSI and NASA NTRS (public NASA documents)", False)]:
        text(s, x + 38, yy, w - 76, 28, lab, 20, C["mute"], mono=True)
        fs = 25 if mono_ else 30
        hh = est_h(val, fs, w - 76, mono=mono_)
        text(s, x + 38, yy + 32, w - 76, hh + 4, val, fs, C["text"], mono=mono_); yy += 32 + hh + 30
    text(s, x + 38, yy, w - 76, 28, "TEAM", 20, C["mute"], mono=True); yy += 34
    for n, r in TEAM:
        text(s, x + 38, yy, w - 76, 40, f"{n}  |  {r}", 26, C["text"]); yy += 46
    text(s, x + 38, 900, w - 76, 70, AI_NOTE, 22, C["mute"])

    # sanity: exactly 7 slides, nothing outside the slide area
    assert len(prs.slides) == 7, len(prs.slides)
    for k, sl in enumerate(prs.slides, 1):
        for sh in sl.shapes:
            if sh.left < 0 or sh.top < 0 or sh.left + sh.width > prs.slide_width + Emu(10) or sh.top + sh.height > prs.slide_height + Emu(10):
                warnings.append(f"slide {k}: shape outside the slide area ({sh.shape_type})")
    prs.save(PPTX_OUT)
    for w_ in warnings:
        print("WARNING", w_)
    return len(prs.slides)


def main() -> int:
    for fn in IMAGES.values():
        if not (SHOTS / fn).is_file():
            print("missing screenshot:", fn); return 1
        cropped(fn)
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(build_html(), encoding="utf-8")
    n_html = build_pdf()
    n_pptx = build_pptx()
    print(f"html slides={n_html}  pptx slides={n_pptx}")
    print("wrote", HTML_OUT.relative_to(ROOT), PDF_OUT.relative_to(ROOT), PPTX_OUT.relative_to(ROOT), sep="\n  ")
    return 0 if n_html == n_pptx == 7 else 1


if __name__ == "__main__":
    sys.exit(main())
