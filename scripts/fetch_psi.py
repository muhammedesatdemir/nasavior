"""Fetch ALL PSI investigation metadata (public, no login) into data/raw/psi_investigations_<date>.json.
Raw dump only; curation into data/investigations.json is done by hand from verified sources."""
import json, datetime, urllib.request, urllib.parse, pathlib

BASE = "https://psi.nasa.gov/geode-py/ws/repo/search"
out, start, total = {}, 0, None
while total is None or start < total:
    qs = urllib.parse.urlencode({"source": "psi", "type": "investigation", "from": start, "size": 50})
    with urllib.request.urlopen(f"{BASE}?{qs}", timeout=60) as r:
        d = json.load(r)
    total = d["hits"]["total"]
    hits = d["hits"]["hits"]
    if not hits:
        break
    for h in hits:
        out[h["_source"]["Accession"]] = h["_source"]
    start += len(hits)
p = pathlib.Path("data/raw") / f"psi_investigations_{datetime.date.today()}.json"
p.write_text(json.dumps(out, indent=1), encoding="utf-8")
print("total reported:", total, "| unique fetched:", len(out), "->", p)
