#!/usr/bin/env python3
"""
Parse all local CFTR1 (CFMDB) mutation-detail pages (raw/mutations/sp-*.html)
into a structured index used to power the client-side search reimplementation.

Captures every field the detail pages carry, handling the label variants that
occur across records (e.g. "Protein Name"; "Phenotype Information" vs
"Submitted Phenotype Details").

Writes data/mutations.json  (list of records)
"""
import glob, json, os, re
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_MUT = os.path.join(ROOT, "raw", "mutations")
DATA = os.path.join(ROOT, "data")

SINGLE = {
    "cDNA Name": "cdna_name",
    "Protein Name": "protein_name",
    "Exon or Intron": "region",
    "Legacy Exon or Intron": "legacy_region",
    "Legacy Name": "legacy_name",
    "Other Details": "other_details",
}
REPEAT = {
    "Contributors": "contributors",
    "Institute": "institute",
    "Submitted Phenotype Details": "phenotype",
    "Phenotype Information": "phenotype",
    "Reference": "reference",
}
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def clean(node):
    txt = node.get_text("\n") if hasattr(node, "get_text") else str(node)
    txt = txt.replace("\xa0", " ")
    lines = [ln.strip() for ln in txt.splitlines()]
    lines = [ln for ln in lines if ln and not ln.startswith("<!--")]
    return "\n".join(lines).strip()


def parse_file(path):
    sp = int(re.search(r"sp-(\d+)", path).group(1))
    html = open(path, encoding="utf-8", errors="ignore").read()
    soup = BeautifulSoup(html, "lxml")

    rec = {"sp_id": sp}
    for k in SINGLE.values():
        rec.setdefault(k, None)
    for k in set(REPEAT.values()):
        rec.setdefault(k, [])

    for tr in soup.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 2:
            continue
        label = clean(tds[0]).split("\n")[0].strip()
        value = clean(tds[1])
        if label in SINGLE:
            if value:
                rec[SINGLE[label]] = value
        elif label in REPEAT:
            key = REPEAT[label]
            if label == "Contributors":
                m = DATE_RE.search(value)
                date = m.group(1) if m else None
                names = DATE_RE.sub("", value).strip().rstrip(",").strip()
                rec[key].append({"names": names, "date": date})
            elif value:
                rec[key].append(value)

    pm = soup.find("a", id="Any")
    rec["pubmed_search_url"] = pm.get("href") if pm else None
    rec["source_url"] = f"http://www.genet.sickkids.on.ca/MutationDetailPage.external?sp={sp}"
    m = re.search(r"last updated at ([A-Za-z]+ \d{1,2}, \d{4})", html)
    rec["db_last_updated"] = m.group(1) if m else None
    return rec


def main():
    os.makedirs(DATA, exist_ok=True)
    files = sorted(glob.glob(os.path.join(RAW_MUT, "sp-*.html")),
                   key=lambda p: int(re.search(r"sp-(\d+)", p).group(1)))
    records = []
    for p in files:
        try:
            r = parse_file(p)
            if r.get("cdna_name") or r.get("legacy_name") or r.get("protein_name"):
                records.append(r)
        except Exception as e:
            print("ERR", p, e)

    with open(os.path.join(DATA, "mutations.json"), "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, separators=(",", ":"))
    # coverage report
    def frac(key):
        n = sum(1 for r in records if r.get(key))
        return f"{n}/{len(records)}"
    print(f"parsed {len(records)} records -> data/mutations.json")
    for k in ["cdna_name", "protein_name", "legacy_name", "region",
              "other_details", "phenotype", "contributors", "institute", "reference"]:
        print(f"  {k}: {frac(k)}")


if __name__ == "__main__":
    main()
