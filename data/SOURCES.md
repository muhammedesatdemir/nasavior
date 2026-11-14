# Data Sources (Phase 0 discovery, 2026-11-14)

## NASA PSI (Physical Sciences Informatics) — metadata, public, no login
- Endpoint used (found in PSI web app bundle): `GET https://psi.nasa.gov/geode-py/ws/repo/search?source=psi&type=investigation&from=<n>&size=<n>`
- Raw dump: `data/raw/psi_investigations_2026-11-14.json` (133 investigations; 25 combustion-related by keyword filter).
- Fields available per investigation: Accession, Title, Acronym, Flight Platform, Objectives, Approach, Hypothesis, Research Impacts/Earth Benefits, Experiment Hardware, Publication list.
- Limitation: ACME measurement data may require authorization; we use investigation metadata only unless a file is public.
- Not found by title in PSI (to be checked in Phase 1): BASS-II, Saffire IV-VI, FLEX-2 detail, CFI. Their facts come from NTRS papers below.

## NASA NTRS — records verified to exist with public PDF (2026-11-14)
| NTRS ID | Title | Use |
|---|---|---|
| 20160000593 | Combustion of Solids in Microgravity: Results from the BASS-II Experiment | Flammability map (0g PMMA O2 x flow) |
| 20130010991 | Evaluating Material Flammability in Microgravity and Martian Gravity Compared to the NASA Standard Normal Gravity Test | Partial-g limits |
| 20160012691 | Correlation of Normal Gravity Mixed Convection Blowoff Limits with Microgravity Forced Flow Blowoff Limits | 1g vs 0g blowoff |
| 20260000646 / 20260001966 | Material Flammability at Lunar and Martian Gravity | g-non-monotonicity warning |
| 20250010653 | Lunar Combustion Investigation: Flammability Results from a Rotating Sounding Rocket | Lunar-g data |
| 20170008805 | Results of Large-Scale Spacecraft Flammability Tests | Saffire-I |
| 20180005168 | Saffire: A Novel Approach to Study of Spacecraft Fire Safety Using Un-Manned Spacecraft | Saffire overview |
| 20210011521 / 20210017780 | Fire Safety Implications of Preliminary Results from Saffire IV and V | Saffire IV/V |
| 20240002981 | Preliminary Results from the Saffire VI Experiment | Saffire VI |
| 20200000557 | Buoyancy Effects on Concurrent Flame Spread Over Thick PMMA | Pressure/buoyancy |
| 20150022421 | Buoyant Effects on the Flammability of Silicone Samples Planned for Saffire | Silicone |
| 20220002714 | Model Development of Large-Scale Spacecraft Fires During Saffire-IV | Modeling |
| 20070018272 | ISS Temperature and Humidity Control Subsystem Verification for Node 1 | ISS cabin airflow |
| 20220011152 / 20240005117 | Exploration Atmospheres (OAF 2022; ICES-2024) | 56.5 kPa / 34% O2 environment |
| 20150004099 / 20110008636 | NASA-STD-6001 Test 1 / flammability limit papers | Limit definitions |

NTRS API: `https://ntrs.nasa.gov/api/citations/search?q=...` and `/api/citations/<id>` work without a key.
Note: "distributionDate" in NTRS is not the publication year; take year from the paper itself.

## Still unverified (do NOT use unless opened and confirmed)
Link et al. 2018 Sci Rep 8:120 (DOI 10.1038/s41598-017-18398-4); Olson & Ferkul 2017 Combust. Flame 180; Urban et al. 2019; Zhao et al. 2017; Sacksteder & T'ien 1994; Ferkul & Olson 2011.
