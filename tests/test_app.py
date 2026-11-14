"""Smoke test: the Streamlit app renders for every environment without exceptions."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.mark.parametrize("env", ["iss", "lunar", "mars", "rover", "earth"])
def test_app_runs_for_each_environment(env):
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, at.exception
    at.radio(key="env").set_value(env).run()
    assert not at.exception, at.exception


def test_ask_tab_answers_without_exception():
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.text_input(key="qbox").set_value("What happened to silicone samples in microgravity?").run()
    assert not at.exception, at.exception
