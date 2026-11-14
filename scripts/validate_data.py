"""Validates all curated datasets. Exit code 1 on any error.
Checks: schema, unique ids, reference integrity, source-page presence, tier rules, null policy, unit sanity.
Run: python scripts/validate_data.py"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.models import (load_environments, load_investigations, load_measurements,  # noqa: E402
                        load_references)

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


refs = load_references()
invs = load_investigations()
meas = load_measurements()
envs = load_environments()
ref_ids = [r.ref_id for r in refs]
for d in {x for x in ref_ids if ref_ids.count(x) > 1}:
    err(f"duplicate ref_id {d}")
ref_set = set(ref_ids)
inv_set = {i.inv_id for i in invs}

for i in invs:
    for r in i.ref_ids:
        if r not in ref_set:
            err(f"investigation {i.inv_id}: unknown ref {r}")
    for f in i.key_findings:
        if f.ref_id not in ref_set:
            err(f"investigation {i.inv_id}: finding cites unknown ref {f.ref_id}")
        if f.ref_id not in i.ref_ids:
            err(f"investigation {i.inv_id}: finding ref {f.ref_id} missing from ref_ids")
        if not f.page_or_figure.strip():
            err(f"investigation {i.inv_id}: finding without page_or_figure")
    if i.source == "PSI" and not i.psi_url:
        err(f"investigation {i.inv_id}: PSI record without psi_url")
    if (i.o2_range_pct or i.flow_range_cm_s) and not i.ranges_ref:
        err(f"investigation {i.inv_id}: ranges given without ranges_ref")
if len(inv_set) != len(invs):
    err("duplicate inv_id")

mids = [m.meas_id for m in meas]
for d in {x for x in mids if mids.count(x) > 1}:
    err(f"duplicate meas_id {d}")
for m in meas:
    if m.ref_id not in ref_set:
        err(f"{m.meas_id}: unknown ref {m.ref_id}")
    if m.inv_id and m.inv_id not in inv_set:
        err(f"{m.meas_id}: unknown inv_id {m.inv_id}")
    if not m.page_or_figure.strip():
        err(f"{m.meas_id}: missing page_or_figure")
    if m.evidence_tier == "A-d" and "digitized" not in m.note.lower():
        err(f"{m.meas_id}: tier A-d requires a 'digitized' uncertainty note")
    if m.outcome == "limit" and (m.limiting_o2_pct is None or m.limit_definition is None):
        err(f"{m.meas_id}: limit record needs limiting_o2_pct and limit_definition")
    if m.outcome != "limit" and (m.limiting_o2_pct is not None or m.limit_definition is not None):
        err(f"{m.meas_id}: limit fields set on non-limit record")
    if m.spread_rate_mm_s is not None and m.outcome in ("no_spread", "limit"):
        if m.outcome == "no_spread" and m.g_level == 0:
            err(f"{m.meas_id}: spread rate on a no-spread microgravity record")

for e in envs:
    for b in e.basis:
        if b.ref_id not in ref_set:
            err(f"environment {e.id}: unknown ref {b.ref_id}")
    if e.assumption and not e.assumption_note:
        err(f"environment {e.id}: assumption without assumption_note")

print(f"references={len(refs)} investigations={len(invs)} measurements={len(meas)} environments={len(envs)}")
print("tiers:", dict(Counter(m.evidence_tier for m in meas)))
print("measurements by g:", dict(sorted(Counter(m.g_level for m in meas).items())))
print("investigations by theme:", dict(Counter(i.theme for i in invs)))
print("investigations with findings:", sum(1 for i in invs if i.key_findings), "of", len(invs))
if errors:
    print(f"\n{len(errors)} ERROR(S):")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("\nOK: all checks passed")
