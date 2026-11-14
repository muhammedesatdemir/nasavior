"""Design-system guards: no emoji anywhere in UI code or data shown to users, no gradients, small radii."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_FILES = [ROOT / "app.py", *sorted((ROOT / "src").rglob("*.py")), ROOT / ".streamlit" / "config.toml"]
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⬆✅❌⚠️]")


def test_no_emoji_in_ui_code():
    bad = [(f.name, m.group()) for f in UI_FILES for m in EMOJI.finditer(f.read_text(encoding="utf-8"))]
    assert not bad, bad


def test_no_emoji_in_user_visible_data():
    for name in ("investigations.json", "references.json", "environments.yaml", "measurements.csv"):
        t = (ROOT / "data" / name).read_text(encoding="utf-8")
        assert not EMOJI.search(t), name


def test_theme_has_no_gradient_and_small_radii():
    css = (ROOT / "src" / "ui" / "theme.py").read_text(encoding="utf-8")
    assert "gradient(" not in css.lower()
    radii = [int(x) for x in re.findall(r"border-radius:\s*(\d+)px", css)]
    assert radii and max(radii) <= 4


def test_theme_tokens_match_spec():
    css = (ROOT / "src" / "ui" / "theme.py").read_text(encoding="utf-8")
    for hexcode in ["#0B0F17", "#111827", "#1F2937", "#F3F4F6", "#9CA3AF", "#38BDF8", "#10B981", "#EF4444", "#F59E0B"]:
        assert hexcode in css, hexcode
