"""Edge cases, hostile input, display hygiene and deploy readiness."""
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.engine import (State, coverage_matrix, environments, gap_statements, material_margins, relevance,
                        summary_points)
from src.qa import answer

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "app.py")


# ---------------------------------------------------------------- engine at the extremes
@pytest.mark.parametrize("g", [0.0, 0.16, 0.38, 1.0, 0.5, 2.0])
@pytest.mark.parametrize("o2", [15.0, 40.0])
@pytest.mark.parametrize("flow", [None, 0.0, 60.0])
def test_engine_never_crashes_at_extremes(g, o2, flow):
    st_ = State(g, o2, 40.0, flow)
    material_margins(st_)
    relevance(st_)
    assert summary_points(st_)  # always at least one sentence
    coverage_matrix()
    assert gap_statements()


# ---------------------------------------------------------------- Q&A with hostile / odd input
HOSTILE = ["", "   ", "???", "<script>alert(1)</script>", "'; DROP TABLE x;--", "a" * 20000, "\u0000\u200b",
           "\u4e2d\u6587\u95ee\u9898", "0.38 g 26 % " * 200, "g g g g", "%%% 100 %", "${jndi:ldap://x}"]


@pytest.mark.parametrize("q", HOSTILE)
def test_qa_is_safe_on_hostile_input(q):
    a = answer(q)
    assert a["status"] in ("ok", "partial", "no_data")
    assert isinstance(a["evidence"], list) and len(a["evidence"]) <= 5
    assert all(p.ref_id and p.page for p in a["evidence"])


def test_qa_no_data_for_empty_and_noise():
    assert answer("")["status"] == "no_data"
    assert answer("???")["status"] == "no_data"


# ---------------------------------------------------------------- the rendered app
# A leak is a missing value rendered as a value ("None %", "nan psi", a bare "None" cell) or an unfilled template.
SENTINELS = re.compile(r"\b(nan|none|null)\s*(%|psi\b|kpa\b|cm/s|mm/s|mm\b)|^\s*(nan|none|null)\s*$|undefined|%s|\{\w+\}|<script",
                       re.I)


def _visible_strings(at):
    out = [m.value for m in at.markdown] + [t.value for t in at.text] + [c.value for c in at.caption]
    out += [str(m.value) for m in at.metric]
    for df in at.dataframe:
        out += [str(v) for v in df.value.astype(str).values.ravel()]
    return out


@pytest.mark.parametrize("env", ["iss", "lunar", "mars", "rover", "earth"])
def test_no_nan_none_or_template_leaks_on_screen(env):
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.radio(key="env").set_value(env).run()
    assert not at.exception
    leaks = [s[:120] for s in _visible_strings(at) if SENTINELS.search(re.sub(r"<style.*?</style>", "", s, flags=re.S))]
    assert not leaks, leaks[:3]


@pytest.mark.parametrize("o2,p,flow", [(15.0, 40.0, 0.0), (40.0, 105.0, 60.0), (15.0, 105.0, 60.0), (40.0, 40.0, 0.0)])
def test_app_survives_extreme_sliders(o2, p, flow):
    at = AppTest.from_file(APP, default_timeout=60).run()
    for env in ("iss", "lunar", "earth"):
        at.radio(key="env").set_value(env).run()
        at.slider(key="o2").set_value(o2)
        at.slider(key="p").set_value(p)
        at.slider(key="flow").set_value(flow)
        at.run()
        assert not at.exception, (env, o2, p, flow)


def test_app_survives_hostile_question():
    at = AppTest.from_file(APP, default_timeout=60).run()
    for q in ["<script>alert(1)</script>", "???", "x" * 400]:
        at.text_input(key="qbox").set_value(q).run()
        assert not at.exception


def test_user_text_is_escaped_in_rendered_html():
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.text_input(key="qbox").set_value('<img src=x onerror=alert(1)> cable').run()
    html_blobs = " ".join(m.value for m in at.markdown)
    assert "<img src=x" not in html_blobs and "onerror=alert" not in html_blobs.replace("&lt;", "")


# ---------------------------------------------------------------- deploy readiness
def test_requirements_are_lean_and_portable():
    req = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    for bad in ("pywin32", "fastembed", "scikit-learn", "torch", "tensorflow", "onnx", "pytest", "pypdf", "playwright"):
        assert bad not in req, bad
    assert all("==" in ln for ln in req.splitlines() if ln.strip() and not ln.startswith("#"))


def test_runtime_code_has_no_windows_paths_or_cwd_dependence():
    runtime = [ROOT / "app.py", *sorted((ROOT / "src").rglob("*.py"))]
    for f in runtime:
        txt = f.read_text(encoding="utf-8")
        assert "C:\\" not in txt and "c:\\" not in txt, f.name
        assert not re.search(r"open\(\s*[\"']data/", txt), f.name   # must resolve via Path(__file__)
    assert "Path(__file__).resolve().parent.parent" in (ROOT / "src" / "models.py").read_text(encoding="utf-8")


def test_runtime_needs_no_api_key_or_network_secrets():
    for f in [ROOT / "app.py", *sorted((ROOT / "src").rglob("*.py"))]:
        txt = f.read_text(encoding="utf-8").lower()
        for bad in ("api_key", "openai", "anthropic", "genai", "os.environ", "st.secrets", "requests.get", "urllib"):
            assert bad not in txt, (f.name, bad)


def test_data_paths_exist_in_repo_layout():
    for name in ("investigations.json", "measurements.csv", "references.json", "environments.yaml"):
        assert (ROOT / "data" / name).is_file(), name
    assert (ROOT / ".streamlit" / "config.toml").is_file()


def test_every_reference_url_is_https_and_well_formed():
    from src.models import load_references
    for r in load_references():
        assert re.match(r"^https://[\w.-]+/[\w./?=&%-]*$", r.url), r.ref_id
        if r.kind == "NTRS":
            assert r.url.endswith(r.ntrs_id), r.ref_id


def test_environment_presets_resolve():
    envs = environments()
    assert set(envs) == {"iss", "lunar", "mars", "rover", "earth"}
