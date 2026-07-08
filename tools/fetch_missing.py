#!/usr/bin/env python3
"""Fetch the sub-resources that the first crawl missed (newsletters, consortium
tables, sequence files, domain image, JS libs) into raw/, preserving paths.
Records each in manifest.jsonl. Skips already-present files."""
import hashlib, json, os, re, time
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
BASE = "http://www.genet.sickkids.on.ca/"
UA = "Mozilla/5.0 (compatible; CFMDB-archival/1.1; preservation copy)"
S = requests.Session(); S.headers.update({"User-Agent": UA})

rep = json.load(open(os.path.join(ROOT, "audit_report.json")))
targets = []
for t in rep["broken_internal"]:
    tt = t.strip()
    if tt.startswith("../mutations/") or "jsessionid" in tt:
        continue  # missing records / session links, handled separately
    targets.append(tt.lstrip("/"))
targets = sorted(set(targets))

mf = open(os.path.join(ROOT, "manifest.jsonl"), "a", encoding="utf-8")
ok = err = skip = 0
results = {"fetched": [], "failed": []}
for rel in targets:
    dest = os.path.join(RAW, rel.replace("/", os.sep))
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        skip += 1; continue
    url = BASE + rel
    try:
        r = S.get(url, timeout=40)
        if r.status_code == 200 and r.content:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "wb").write(r.content)
            mf.write(json.dumps({"url": url, "path": rel, "status": 200,
                     "bytes": len(r.content),
                     "sha256": hashlib.sha256(r.content).hexdigest(),
                     "note": "missing-resource"}) + "\n")
            ok += 1; results["fetched"].append(rel)
        else:
            err += 1; results["failed"].append(f"{rel} [HTTP {r.status_code}]")
        time.sleep(0.15)
    except Exception as e:
        err += 1; results["failed"].append(f"{rel} [{e}]")
mf.close()
print(f"fetched={ok} skipped={skip} failed={err} (of {len(targets)} targets)")
if results["failed"]:
    print("FAILED:")
    for f in results["failed"]: print("  ", f)
json.dump(results, open(os.path.join(ROOT, "fetch_missing_result.json"), "w"), indent=2)
