#!/usr/bin/env python3
"""Second-pass fetch: resolve each still-broken internal link RELATIVE to the
page that references it, and pull it from the live server into raw/.
Handles the newsletter GIFs and consortium-table images/sub-pages that live in
sub-directories. Skips dynamic (empty) .txt endpoints, dead cgi, and missing
mutation records."""
import hashlib, json, os, posixpath, re, time
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
BASE = "http://www.genet.sickkids.on.ca/"
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (archival)"})

rep = json.load(open(os.path.join(ROOT, "audit_report.json")))
jobs = {}  # resolved_rel_path -> url
for target, pages in rep["broken_internal"].items():
    t = target.strip()
    if t.startswith("../mutations/") or "cgi-bin" in t or t.endswith(
            (".txt",)) or "jsessionid" in t:
        continue
    ref = pages[0]  # first referencing page, repo-relative under site/
    if t.startswith("/"):
        rel = t.lstrip("/")
    else:
        rel = posixpath.normpath(posixpath.join(posixpath.dirname(ref), t))
    if rel.startswith("..") or "mutations/" in rel:
        continue
    jobs[rel] = BASE + rel

mf = open(os.path.join(ROOT, "manifest.jsonl"), "a", encoding="utf-8")
ok = err = skip = 0
failed = []
for rel, url in sorted(jobs.items()):
    dest = os.path.join(RAW, rel.replace("/", os.sep))
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        skip += 1; continue
    try:
        r = S.get(url, timeout=40)
        if r.status_code == 200 and r.content:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "wb").write(r.content)
            mf.write(json.dumps({"url": url, "path": rel, "status": 200,
                     "bytes": len(r.content),
                     "sha256": hashlib.sha256(r.content).hexdigest(),
                     "note": "missing-resource-2"}) + "\n")
            ok += 1
        else:
            err += 1; failed.append(f"{rel} [HTTP {r.status_code} bytes {len(r.content)}]")
        time.sleep(0.12)
    except Exception as e:
        err += 1; failed.append(f"{rel} [{e}]")
mf.close()
print(f"pass2 fetched={ok} skipped={skip} failed={err} (of {len(jobs)} targets)")
for f in failed:
    print("  FAIL", f)
