# Space Apps 2026 submission text (copy and paste)

Fields marked `<<...>>` must be filled in by the team before submitting. Re-check every field name against the live project form; the names below follow the Project Submission Guide.

---

## Project Name

Nasavior

## Challenge

Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data

## Demo link (video, 30 seconds or less, English or English subtitles)

`<<public video URL, no login>>`

## Final Project link

`<<GitHub repository URL>>` and live app `<<Streamlit Community Cloud URL>>`

---

## High-Level Summary

Nasavior is an interactive atlas of NASA microgravity combustion experiments for engineers planning spacecraft, stations, Moon and Mars habitats and pressurized rovers. The user picks an environment and sets oxygen, pressure and air flow. Nasavior then shows which NASA experiments are relevant, the oxygen limits NASA actually measured at that gravity, where a material burned in 0 g but not in 1 g (or the reverse), and where NASA has no data. Every number is transcribed from a NASA document and displayed with its reference and page. Nothing is extrapolated or generated, so the Moon and Mars data gap is shown honestly instead of being filled in.

## Project Details

**The problem.** NASA screens spacecraft materials with a 1 g flammability test (NASA-STD-6001 Test 1). NASA's own research shows that this is not always conservative: some materials keep burning at lower oxygen in reduced gravity. The relevant data is spread across PSI records, conference papers and posters, and almost none of it covers the atmospheres planned for lunar and Martian habitats.

**What Nasavior does.**
- *Overview:* compares the selected oxygen level with measured limits at the same gravity level and ranks the experiments whose recorded conditions match the selection.
- *Flammability:* limiting oxygen by gravity level (0, 0.16, 0.38, 1 g), a map of every tested oxygen and flow condition, and a sample-by-sample 0 g versus 1 g comparison.
- *Investigation Atlas:* 26 experiments (24 PSI investigations plus 2 NTRS entries) with objectives, hardware, platforms, cited findings and PSI links, filterable by theme and text.
- *Lunar & Mars gap:* a coverage matrix that counts source-cited records per gravity level and condition, so the missing data is visible.
- *Ask the Atlas:* a search box over the dataset. Answers are copied from records and show their source; if nothing matches, or the question names something the dataset never mentions (for example cable insulation), it says so.
- *Earth benefits:* NASA PSI's own statements of terrestrial benefit.

**Findings the data supports.**
- BASS-II on the ISS: a PMMA rod kept burning at 13.6 % oxygen in microgravity, while its 1 g blowoff limit is 16 %, a negative margin of 2.4 % oxygen.
- Saffire-II: silicone samples from 0.27 to 1.03 mm did not spread a flame in microgravity at 20 cm/s although the thinnest one burned completely in 1 g. Reduced gravity is not always worse, which is why a per-material, per-gravity view matters.
- Drop-tower tests at Martian and Lunar gravity gave negative oxygen margins versus 1 g for Mylar, Ultem and Nomex.
- All 0.16 g and 0.38 g records are 5-second drop tests, none lies inside the lunar atmosphere envelope (oxygen at or above 30 %, pressure at or below 10.2 psi), and PSI holds no partial-gravity combustion data. NASA plans the first combustion experiments on the Moon (FM2) for late 2026.

**Design principle.** A tool that could mislead a safety decision must never invent a value. Nasavior therefore stores only what a source prints, shows the gravity level a limit was measured at, flags assumptions (the Mars habitat and rover atmospheres are not defined by the sources), and treats "no data" as a result.

## How We Used NASA Data

- **NASA PSI (Physical Sciences Informatics):** metadata of 24 combustion investigations (ACME, BASS, BASS-II, CFI, DAFT, FLEX, FLEX-2, SAME, SAME-R, SLICE, SPICE, Saffire-I, II and III and PSI-hosted ground studies that reuse flight data), retrieved from the public API behind psi.nasa.gov on 14 November 2026. Objectives, hardware, platforms and Earth-benefit texts are copied from PSI and attributed to each record.
- **NASA NTRS (Technical Reports Server):** values transcribed by hand with page or table numbers from the BASS-II poster (20160000593), Olson and Ferkul 2012 (20130010991), Marcum et al. 2016 (20160012691), Ferkul et al. 2026 (20260000646), the LUCI sounding rocket results (20250010653), Saffire I-III (20170008805), Saffire IV-V (20210011521), Saffire VI (20240002981), ISS Node 1 air velocity (20070018272) and the Exploration Atmospheres validation study (20220011152).
- **Result:** 55 source-cited measurement records, 26 Atlas entries, 35 references, 5 environment presets with their basis.

## Space Agency Partner Data and References

All data are NASA public documents. References with links are in `data/references.json` and in the About tab of the app.

Third-party software: Streamlit, Plotly, pandas, NumPy, pydantic, PyYAML, rank-bm25, scikit-learn, pytest (open source). Fonts: Inter and JetBrains Mono (Google Fonts, open license). No NASA logos or branding are used. No images are used.

## Known Limitations

- Reduced-gravity limits (0.16 g, 0.38 g) come only from drop-tower tests of 5.18 s with criteria that differ from 1 g, as stated by the source.
- Saffire I-III Table I gives no pressure; the field is left empty.
- Saffire VI per-sample heat release, CO and CO2 columns were garbled in text extraction and are not used.
- PSI investigation links follow the PSI web-app route and were not browser-tested.
- The relevance ranking is a search aid, not a hazard score.
- Olson and Ferkul 2012 contradicts itself between its Conclusions and its Table I; Table I is used.
- 20 of the 26 Atlas entries show the PSI objective text only; no quantitative findings were extracted for them.
- The Mars habitat and rover atmospheres are assumptions (the exploration atmosphere is used as a stand-in) and are flagged as such in the app.

## Use of SI (AI)

Code was written with the help of an AI coding assistant (Claude Code, Anthropic), including help with architecture proposals, data-extraction scripts and tests. The team set the scope, chose the sources, reviewed the extracted values against the documents and decided what the product may and may not claim. The application contains no generative model at run time: search is BM25 retrieval over the cited dataset, and answers are copied from records. The project uses no AI-generated images, video or NASA branding. `<<Team: confirm this paragraph is accurate before submitting.>>`

## Team

`<<names and roles>>`

---

## 30-second video script (hard limit: 30 seconds, add English captions)

Recording setup: browser at 1920x1080, app zoom 100 %, light screen movement only. Record voice-over separately, about 2.3 words per second, and cut to 30 seconds or less. Check the exported file length before upload.

| Time | Screen | Voice-over |
|---|---|---|
| 0-5 s | Title card: NASAVIOR, Flame in Freefall, Space Apps 2026 | "Passing a fire test on Earth does not mean a material is safe in space." |
| 5-12 s | Select ISS in the sidebar, open Flammability tab, limits chart and O2 x flow map appear | "Nasavior puts NASA's microgravity combustion experiments in one cited atlas." |
| 12-20 s | Highlight the BASS-II card and the silicone row in the 0 g versus 1 g table | "On the ISS, PMMA kept burning at 13.6 percent oxygen. On Earth the limit is 16." |
| 20-27 s | Select Lunar Base, open Lunar & Mars gap tab, amber zeros in the coverage matrix | "For the Moon and Mars, NASA's data stops at five-second drop tests. Nasavior shows exactly where." |
| 27-30 s | End card: repository and app URL, team name | "Nasavior. Know what NASA knows." |

Voice-over word count: 62 words (about 27 seconds at 2.3 words per second, leaving a margin under the 30-second limit). Do not add words.

### Backup if a video is not accepted: 7-slide outline

1. Title and one-line claim. 2. The problem (1 g screening is not always conservative). 3. What NASA measured (BASS-II, Saffire-II silicone). 4. How Nasavior works (environment, limits, relevance). 5. The Moon and Mars gap (coverage matrix). 6. How we kept it honest (citations, no extrapolation, known limitations). 7. Links and team.
