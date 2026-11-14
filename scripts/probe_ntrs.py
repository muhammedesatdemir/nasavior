"""Probe NTRS records: title, year, open-access PDF availability. Dev helper for Phase 0."""
import json, sys, urllib.request

IDS = sys.argv[1:]
for i in IDS:
    try:
        with urllib.request.urlopen(f"https://ntrs.nasa.gov/api/citations/{i}", timeout=30) as r:
            d = json.load(r)
    except Exception as e:
        print(i, "ERR", e); continue
    pdfs = [x.get("links", {}).get("pdf") for x in d.get("downloads", [])]
    print(f"{i} | {d.get('title')} | {d.get('distributionDate','')[:4]} | public={d.get('distribution')} | pdf={'yes' if any(pdfs) else 'no'} | doi={[x.get('identifier') for x in d.get('otherIdentifiers',[]) if 'DOI' in str(x)] or '-'}")
