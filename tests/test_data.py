"""Data integrity tests: the curated NASA datasets load, validate, and keep their provenance."""
import pytest
from pydantic import ValidationError

from src.models import (Measurement, load_environments, load_investigations, load_measurements,
                        load_references)


def test_datasets_load():
    assert len(load_references()) >= 11
    assert len(load_investigations()) >= 20
    assert len(load_measurements()) >= 40
    assert len(load_environments()) == 5


def test_every_measurement_has_source_and_location():
    refs = {r.ref_id for r in load_references()}
    for m in load_measurements():
        assert m.ref_id in refs, m.meas_id
        assert m.page_or_figure.strip(), m.meas_id


def test_partial_gravity_data_comes_only_from_cited_tables():
    partial = [m for m in load_measurements() if 0 < m.g_level < 1]
    assert partial, "expected Lunar/Martian drop-tower limits"
    assert {m.ref_id for m in partial} == {"REF-OLSON2012"}
    assert {m.g_level for m in partial} == {0.16, 0.38}


def test_olson_table_spot_values():
    ms = {m.meas_id: m for m in load_measurements()}
    mylar_1g_uloi = next(m for m in ms.values() if m.material == "Mylar G" and m.g_level == 1.0
                         and m.limit_definition == "ULOI")
    assert mylar_1g_uloi.limiting_o2_pct == 21.2
    mylar_lunar = next(m for m in ms.values() if m.material == "Mylar G" and m.g_level == 0.16
                       and m.limit_definition == "ULOI_dropstar")
    assert mylar_lunar.limiting_o2_pct == 15.6


def test_bass2_negative_margin_is_consistent():
    ms = [m for m in load_measurements() if m.inv_id == "PSI-25"]
    ug = next(m for m in ms if m.g_level == 0)
    one_g = next(m for m in ms if m.g_level == 1)
    assert round(one_g.limiting_o2_pct - ug.limiting_o2_pct, 1) == 2.4  # source: 2.4% O2 margin


def test_out_of_range_rejected():
    base = dict(meas_id="x", material="m", geometry="g", spread_mode="concurrent", g_level=0, platform="ISS",
                outcome="burn", evidence_tier="A", ref_id="r", page_or_figure="p")
    Measurement(**base)
    with pytest.raises(ValidationError):
        Measurement(**{**base, "g_level": -1})
    with pytest.raises(ValidationError):
        Measurement(**{**base, "o2_mole_pct": 5})
    with pytest.raises(ValidationError):
        Measurement(**{**base, "evidence_tier": "Z"})


def test_assumed_environments_are_flagged():
    envs = {e.id: e for e in load_environments()}
    assert envs["mars"].assumption and envs["rover"].assumption
    assert not envs["iss"].assumption
