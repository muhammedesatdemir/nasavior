from src.engine import (State, coverage_matrix, environments, gap_statements, gravity_margin, limit_table,
                        margin_status, material_margins, paired_comparison, relevance)
from src.qa import answer


def test_margin_status_thresholds():
    assert margin_status(25, 24, 23) == "burns"
    assert margin_status(23.5, 24, 23) == "uncertain"
    assert margin_status(22, 24, 23) == "extinguishes"


def test_margins_use_same_gravity_only():
    envs = environments()
    st = State(0.16, envs["lunar"].o2_pct, envs["lunar"].pressure_kpa)
    m = material_margins(st)
    assert set(m["g_level"]) == {0.16}
    assert set(m["material"]) == {"Mylar G", "Ultem 1000", "Nomex HT90-40"}
    # 30 % O2 is above every measured lunar ULOI* -> flame survived in tests
    assert (m["status"] == "burns").all()


def test_no_limit_data_for_unmeasured_gravity():
    assert material_margins(State(0.5, 21, 101.3)).empty


def test_gravity_margin_matches_source_table():
    # Olson & Ferkul Table I: Mylar Martian dO2 = -3.1, Lunar -5.75, 0g -4.1
    gm = gravity_margin("Mylar G").set_index("g_level")["delta_o2"]
    assert gm[0.38] == -3.1 and gm[0.16] == -5.75 and gm[0.0] == -4.1


def test_silicone_burns_in_1g_not_in_0g():
    p = paired_comparison()
    sil = p[p["material"] == "Silicone sheet"]
    assert (sil["verdict"].str.contains("did NOT spread in 0g") | (sil["outcome_1g"] == "no_spread")).all()
    assert (sil["outcome_0g"] == "no_spread").all()


def test_coverage_exposes_partial_g_gap():
    cov = coverage_matrix().set_index("g_level")
    assert cov.loc[0.16, "lunar_envelope_tests"] == 0
    assert cov.loc[0.38, "lunar_envelope_tests"] == 0
    assert cov.loc[0.0, "lunar_envelope_tests"] >= 2  # Saffire VI
    assert len(gap_statements()) >= 3


def test_relevance_prefers_matching_gravity():
    rel = relevance(State(0.0, 22, 100, 20))
    assert rel.iloc[0]["score"] >= rel.iloc[-1]["score"]
    assert rel[rel["inv_id"] == "PSI-99"].iloc[0]["score"] > 0


def test_limit_table_pairs_uloi_moc():
    lt = limit_table()
    assert (lt["uloi"] >= lt["moc"]).all()


def test_qa_cites_every_evidence():
    a = answer("What happened to silicone samples in microgravity?")
    assert a["status"] == "ok"
    for p in a["evidence"]:
        assert p.ref_id and p.page


def test_qa_refuses_when_no_data():
    a = answer("xyzzy plugh quantum banana")
    assert a["status"] == "no_data" and not a["evidence"]


def test_qa_flags_missing_partial_g_cable_data():
    a = answer("Is there data for cable insulation at 0.38 g and 26 % oxygen?")
    assert any("drop-tower" in n or "No record" in n for n in a["notes"])
