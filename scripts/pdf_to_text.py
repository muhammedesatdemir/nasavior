"""Dev helper: download NTRS PDFs (public) and extract text for manual curation. Output stays in data/raw (not shipped as dataset)."""
import sys, json, urllib.request, pathlib
from pypdf import PdfReader
for i in sys.argv[1:]:
    pdf = pathlib.Path(f"data/raw/pdf/{i}.pdf")
    if not pdf.exists():
        meta = json.load(urllib.request.urlopen(f"https://ntrs.nasa.gov/api/citations/{i}", timeout=30))
        url = next(x["links"]["pdf"] for x in meta["downloads"] if x.get("links", {}).get("pdf"))
        if url.startswith("/"): url = "https://ntrs.nasa.gov" + url
        pdf.write_bytes(urllib.request.urlopen(url, timeout=120).read())
    r = PdfReader(str(pdf))
    def page_text(p):
        try:
            return p.extract_text() or ""
        except Exception as e:
            return f"[page extraction failed: {type(e).__name__}]"
    txt = "\n".join(f"\n=====PAGE {n+1}=====\n" + page_text(p) for n, p in enumerate(r.pages))
    pathlib.Path(f"data/raw/txt/{i}.txt").write_text(txt, encoding="utf-8")
    print(i, "pages", len(r.pages), "chars", len(txt))
