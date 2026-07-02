#!/usr/bin/env python3
"""
Capture the DYNAMIC parts of the CFMDB that a plain mirror misses, while the
original server is still up:

  1. Graphic Search
     - the overview gene image  /overviewImage.svc?imageWidth=760.0
     - every region drill-down page  PicturePage.html?domain_id=<X>  (55 regions)
     - each region page's own rendered image(s) (further *.svc calls)
  2. Search-backend-only fields (not present on detail pages)
     - a wildcard Basic Text Search that returns EVERY record, to harvest each
       mutation's Region, Nucleotide Change (Description) and Consequence
     - per-type Criteria/Advanced searches to tag structural + functional type

Saves raw captures under raw/dynamic/ and a harvested table to data/harvest.json.
Tapestry forms are session-bound: we GET the form page first (fresh jsessionid +
seedids/formids), then POST with the same session.
"""
import html as htmllib
import json, os, re, time
import requests
from urllib.parse import urljoin

BASE = "http://www.genet.sickkids.on.ca/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
DYN = os.path.join(RAW, "dynamic")
DATA = os.path.join(ROOT, "data")
UA = "Mozilla/5.0 (compatible; CFMDB-archival/1.0; preservation copy)"
DELAY = 0.3

DOMAIN_IDS = ["0"] + [str(i) for i in range(1, 28)] + [f"i{i}" for i in range(1, 28)]

s = requests.Session()
s.headers.update({"User-Agent": UA})


def save(path, data):
    full = os.path.join(DYN, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode("utf-8"))


def get(url):
    r = s.get(url, timeout=45)
    time.sleep(DELAY)
    return r


def svc_name(url):
    """Deterministic local filename for a *.svc image URL."""
    m = re.search(r"/([^/?]+\.svc)\?(.*)$", url)
    base = m.group(1) if m else re.sub(r"[^A-Za-z0-9.]", "_", url)
    q = re.sub(r"[^A-Za-z0-9]", "_", m.group(2)) if m else ""
    return f"{base}__{q}.img"


def capture_graphic():
    print("[graphic] overview image")
    r = get(urljoin(BASE, "overviewImage.svc?imageWidth=760.0"))
    save("overviewImage.svc__imageWidth_760_0.img", r.content)
    seen_svc = {"overviewImage.svc__imageWidth_760_0.img"}
    for did in DOMAIN_IDS:
        r = get(urljoin(BASE, f"PicturePage.html?domain_id={did}"))
        save(f"PicturePage__domain_id_{did}.html", r.content)
        imgs = set(re.findall(r'(?:src|href)="([^"]*\.svc[^"]*)"', r.text))
        nnew = 0
        for iu in imgs:
            absu = urljoin(BASE, htmllib.unescape(iu))
            name = svc_name(absu)
            if name in seen_svc:
                continue
            seen_svc.add(name)
            ir = get(absu)
            save(name, ir.content)
            nnew += 1
        print(f"  domain_id={did}: {len(r.content)}B, {nnew} new images")


def form_state(page_path, form_id):
    """GET a search page and pull the Tapestry hidden state for a given form."""
    r = get(urljoin(BASE, page_path))
    txt = r.text
    # isolate the form block
    m = re.search(rf'<form[^>]*id="{form_id}".*?</form>', txt, re.S)
    block = m.group(0) if m else txt
    def val(name):
        mm = re.search(rf'name="{name}"[^>]*value="([^"]*)"', block)
        return htmllib.unescape(mm.group(1)) if mm else ""
    action = re.search(r'action="([^"]*)"', block)
    return {
        "action": htmllib.unescape(action.group(1)) if action else "",
        "formids": val("formids"),
        "seedids": val("seedids"),
    }


def parse_result_rows(html_text):
    """Extract (sp_id, cdna, protein, legacy, region, description, consequence)
    from a Basic-search result table."""
    rows = []
    for blk in re.findall(r'<tr>(.*?)</tr>', html_text, re.S):
        sp = re.search(r'MutationDetailPage\.external\?sp=(\d+)', blk)
        if not sp:
            continue
        cells = re.findall(r'<td[^>]*>(.*?)</td>', blk, re.S)
        def txt(i):
            if i >= len(cells):
                return ""
            t = re.sub(r'<[^>]+>', ' ', cells[i])
            return htmllib.unescape(re.sub(r'\s+', ' ', t)).strip()
        rows.append({
            "sp_id": int(sp.group(1)),
            "cdna_name": txt(0), "protein_name": txt(1), "legacy_name": txt(2),
            "region": txt(3), "nucleotide_change": txt(4), "consequence": txt(5),
        })
    return rows


def harvest_all_rows():
    """Basic search, field=All Fields, term that every record contains, to pull
    the full result table (Region / Nucleotide Change / Consequence)."""
    print("[harvest] wildcard basic search")
    st = form_state("SearchPage.html", "Form")
    action = urljoin(BASE, st["action"])
    best = []
    for field, term in [("cdnaName", "c"), ("", "a"), ("cdnaName", ".")]:
        data = {
            "formids": st["formids"], "seedids": st["seedids"],
            "submitmode": "", "submitname": "",
            "PropertySelection": field, "mutationSearchValue": term,
        }
        r = s.post(action, data=data, timeout=90)
        time.sleep(DELAY)
        rows = parse_result_rows(r.text)
        save(f"basicsearch_{field or 'all'}_{term}.html", r.content)
        print(f"  field={field or 'ALL'} term={term!r} -> {len(rows)} rows")
        if len(rows) > len(best):
            best = rows
    return best


def main():
    os.makedirs(DYN, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    capture_graphic()
    rows = harvest_all_rows()
    by_sp = {r["sp_id"]: r for r in rows}
    with open(os.path.join(DATA, "harvest.json"), "w", encoding="utf-8") as f:
        json.dump({"rows": list(by_sp.values())}, f, ensure_ascii=False)
    print(f"[done] harvested {len(by_sp)} unique records -> data/harvest.json")


if __name__ == "__main__":
    main()
