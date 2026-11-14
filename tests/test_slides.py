"""Space Apps slide rules: exactly 7 slides, 16:9, no NASA logo, no emoji, no garbled text."""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "docs" / "Nasavior_SpaceApps2026_Slides.pdf"
PPTX = ROOT / "docs" / "Nasavior_SpaceApps2026_Slides.pptx"
HTML = ROOT / "docs" / "slides" / "nasavior_deck.html"
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿️]")


def test_pdf_has_exactly_seven_16x9_pages():
    pypdf = pytest.importorskip("pypdf")
    r = pypdf.PdfReader(str(PDF))
    assert len(r.pages) == 7
    w, h = (float(x) for x in r.pages[0].mediabox[2:])
    assert abs(w / h - 16 / 9) < 0.01


def test_pptx_has_exactly_seven_16x9_slides():
    pptx = pytest.importorskip("pptx")
    prs = pptx.Presentation(str(PPTX))
    assert len(prs.slides) == 7
    assert abs(prs.slide_width / prs.slide_height - 16 / 9) < 0.01


def test_html_has_seven_slides_no_emoji_no_logo_no_garbage():
    html = HTML.read_text(encoding="utf-8")
    assert html.count('class="slide"') == 7
    assert not EMOJI.search(html)
    assert "00a0" not in html and "\x00" not in html
    assert not re.search(r"<img[^>]+(logo|meatball|worm)", html, re.I)


def test_slide_numbers_match_data():
    html = HTML.read_text(encoding="utf-8")
    assert ">55<" in html and ">26<" in html
    assert "https://github.com/muhammedesatdemir/nasavior" in html and "https://nasavior.streamlit.app" in html
