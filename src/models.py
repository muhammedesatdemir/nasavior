"""Typed data layer for Nasavior: loads and validates the curated NASA-sourced datasets."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

DATA = Path(__file__).resolve().parent.parent / "data"

Platform = Literal["ISS", "Cygnus", "drop_tower", "sounding_rocket", "ground_1g"]
Outcome = Literal["burn", "no_spread", "anchored", "partial", "limit", "no_ignition", "extinguished"]
LimitDef = Literal["ULOI", "MOC", "ULOI_dropstar", "MOC_dropstar", "blowoff_1g", "lowest_burn_ug"]
Tier = Literal["A", "A-d", "B"]  # C ("no data") is never stored; it is a computed gap state
Theme = Literal["material_flammability", "smoke_detection", "suppression", "fundamental_combustion",
                "modeling_data_reuse"]


class Reference(BaseModel):
    ref_id: str
    ntrs_id: Optional[str] = None
    title: str
    authors: str
    venue: str
    year: Optional[int] = None
    url: str
    kind: Literal["NTRS", "PSI", "WEB"]


class KeyFinding(BaseModel):
    text: str
    ref_id: str
    page_or_figure: str


class Investigation(BaseModel):
    inv_id: str
    source: Literal["PSI", "NTRS"]
    name: str
    acronym: Optional[str] = None
    platform: Optional[str] = None
    hardware: Optional[str] = None
    objective: str
    impact: Optional[str] = None  # PSI 'Research Impacts/Earth Benefits' text, copied
    o2_range_pct: Optional[str] = None
    pressure_range_kpa: Optional[str] = None
    flow_range_cm_s: Optional[str] = None
    ranges_ref: Optional[str] = None
    key_findings: list[KeyFinding] = Field(default_factory=list)
    ref_ids: list[str]
    psi_url: Optional[str] = None
    theme: Theme
    equipment_theme: Literal["prevention", "detection", "suppression", "fundamentals", "modeling"]


class Measurement(BaseModel):
    meas_id: str
    inv_id: Optional[str] = None
    material: str
    thickness_mm: Optional[float] = None
    geometry: str
    spread_mode: Literal["concurrent", "opposed"]
    g_level: float = Field(ge=0)
    platform: Platform
    test_duration_s: Optional[float] = None
    pressure_kpa: Optional[float] = Field(default=None, gt=0)
    o2_mole_pct: Optional[float] = Field(default=None, ge=10, le=100)
    flow_velocity_cm_s: Optional[float] = Field(default=None, ge=0)
    outcome: Outcome
    spread_rate_mm_s: Optional[float] = Field(default=None, ge=0)
    flame_length_cm: Optional[float] = Field(default=None, ge=0)
    limiting_o2_pct: Optional[float] = Field(default=None, ge=10, le=100)
    limit_definition: Optional[LimitDef] = None
    evidence_tier: Tier
    ref_id: str
    page_or_figure: str
    note: str = ""

    @field_validator("*", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return None if v == "" else v


class EnvBasis(BaseModel):
    ref_id: str
    page: str
    note: str


class Environment(BaseModel):
    id: str
    label: str
    g_level: float = Field(ge=0)
    pressure_kpa: float = Field(gt=0)
    o2_pct: float = Field(ge=10, le=100)
    flow_cm_s: Optional[float] = None
    flow_note: str
    basis: list[EnvBasis]
    assumption: bool
    assumption_note: Optional[str] = None


def load_references() -> list[Reference]:
    return [Reference(**r) for r in json.loads((DATA / "references.json").read_text(encoding="utf-8"))]


def load_investigations() -> list[Investigation]:
    return [Investigation(**r) for r in json.loads((DATA / "investigations.json").read_text(encoding="utf-8"))]


def load_measurements() -> list[Measurement]:
    with (DATA / "measurements.csv").open(encoding="utf-8", newline="") as f:
        return [Measurement(**row) for row in csv.DictReader(f)]


def load_environments() -> list[Environment]:
    doc = yaml.safe_load((DATA / "environments.yaml").read_text(encoding="utf-8"))
    return [Environment(**e) for e in doc["environments"]]
