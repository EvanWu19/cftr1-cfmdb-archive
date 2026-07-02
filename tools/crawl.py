#!/usr/bin/env python3
"""
Faithful crawler for the CFTR1 / Cystic Fibrosis Mutation Database (CFMDB)
hosted at http://www.genet.sickkids.on.ca (retiring).

Downloads:
  - all top-level static Tapestry pages
  - all referenced assets (css/js/images/downloads)
  - every mutation detail page via the stateless ExternalLink service
    MutationDetailPage.external?sp=<ID>

Everything is stored under raw/ preserving the server's exact bytes, plus a
manifest.jsonl recording url -> local path, http status, size, sha256.

Polite: single connection, small delay, retries. Resumable: skips files that
already exist with non-empty content.
"""
import hashlib, json, os, re, sys, time
import requests
from urllib.parse import urljoin, urlparse, parse_qs

BASE = "http://www.genet.sickkids.on.ca/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
MANIFEST = os.path.join(ROOT, "manifest.jsonl")
UA = "Mozilla/5.0 (compatible; CFMDB-archival/1.0; preservation copy)"
DELAY = 0.25
MAX_SP = 2260   # valid detail-page IDs observed to end just above 2200

STATIC_PAGES = [
    "Home.html", "AdvancedSearchPage.html", "CftrDomainPage.html",
    "ConsortiumBackgroundPage.html", "ConsortiumDataPage1.html",
    "ConsortiumGuidelinesPage.html", "Contact.html",
    "GenomicDnaSequencePage.html", "HelpPage.html", "LinkPage.html",
    "MRnaPolypeptideSequencePage.html", "MutationSearch.html",
    "NewsLetters.html", "PicturePage.html", "SearchPage.html",
    "StatisticsPage.html", "SubmitPage.html", "Team.html",
]
ASSETS = [
    "include/main.css", "include/mutationSearch.css", "include/forms.css",
    "include/phoenix.css", "include/institution.css",
    "include/mutationSubmission.css",
    "assets/static/dojo-0.4.3-custom-4.1.6/dojo.js",
    "assets/static/dojo-0.4.3-custom-4.1.6/dojo2.js",
    "assets/static/tapestry-4.1.6/core.js",
    "image/mutationlogo.gif", "image/sumhorsa.gif",
    "download/mouse_cftr_genomic.doc",
]

session = requests.Session()
session.headers.update({"User-Agent": UA})

def rel_for(url):
    """Map an absolute URL to a local path under raw/."""
    p = urlparse(url)
    path = p.path.lstrip("/")
    if not path:
        path = "index.html"
    q = parse_qs(p.query)
    if "sp" in q:  # MutationDetailPage.external?sp=N -> mutations/sp-N.html
        return os.path.join("mutations", f"sp-{q['sp'][0]}.html")
    return path

def fetch(url, dest, manifest_fh, note=""):
    full = os.path.join(RAW, dest)
    if os.path.exists(full) and os.path.getsize(full) > 0:
        return "skip", os.path.getsize(full)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    for attempt in range(4):
        try:
            r = session.get(url, timeout=40)
            data = r.content
            with open(full, "wb") as f:
                f.write(data)
            sha = hashlib.sha256(data).hexdigest()
            manifest_fh.write(json.dumps({
                "url": url, "path": dest.replace("\\", "/"),
                "status": r.status_code, "bytes": len(data),
                "sha256": sha, "note": note,
            }) + "\n")
            manifest_fh.flush()
            time.sleep(DELAY)
            return r.status_code, len(data)
        except Exception as e:
            if attempt == 3:
                manifest_fh.write(json.dumps({
                    "url": url, "path": dest.replace("\\", "/"),
                    "status": "ERROR", "error": str(e), "note": note}) + "\n")
                manifest_fh.flush()
                return "ERROR", 0
            time.sleep(1.5 * (attempt + 1))

def is_valid_detail(path):
    try:
        with open(os.path.join(RAW, path), "rb") as f:
            return b"cDNA Name" in f.read()
    except OSError:
        return False

def main():
    os.makedirs(RAW, exist_ok=True)
    mf = open(MANIFEST, "a", encoding="utf-8")
    counts = {"static": 0, "asset": 0, "detail_valid": 0, "detail_empty": 0, "error": 0}

    print("[1/3] static pages")
    for pg in STATIC_PAGES:
        st, sz = fetch(urljoin(BASE, pg), pg, mf, "static")
        counts["static"] += 1
        print(f"  {pg}: {st} {sz}")

    print("[2/3] assets")
    for a in ASSETS:
        st, sz = fetch(urljoin(BASE, a), a, mf, "asset")
        counts["asset"] += 1
        print(f"  {a}: {st} {sz}")

    print(f"[3/3] mutation detail pages sp=1..{MAX_SP}")
    for sp in range(1, MAX_SP + 1):
        url = f"{BASE}MutationDetailPage.external?sp={sp}"
        dest = os.path.join("mutations", f"sp-{sp}.html")
        st, sz = fetch(url, dest, mf, "detail")
        if st == "ERROR":
            counts["error"] += 1
        elif is_valid_detail(dest):
            counts["detail_valid"] += 1
        else:
            counts["detail_empty"] += 1
            # remove empty template pages so the archive holds only real records
            try:
                os.remove(os.path.join(RAW, dest))
            except OSError:
                pass
        if sp % 100 == 0:
            print(f"  ...sp={sp} valid={counts['detail_valid']} empty={counts['detail_empty']} err={counts['error']}")

    mf.close()
    print("DONE", json.dumps(counts))
    with open(os.path.join(ROOT, "crawl_summary.json"), "w") as f:
        json.dump(counts, f, indent=2)

if __name__ == "__main__":
    main()
