#!/usr/bin/env python3
"""
Exhaustive static audit of the reconstructed site/.
For every .html file, extract every href / src / <area href> / <form action> /
CSS url(...) and verify internal targets resolve to a real local file.
Reports broken internal links, un-converted dynamic endpoints, and the set of
external URLs (for separate live checking).
"""
import glob, json, os, re, collections
from urllib.parse import urljoin, urldefrag, unquote
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

broken = collections.defaultdict(list)     # target -> [pages]
dynamic = collections.defaultdict(list)    # suspicious dynamic endpoint -> [pages]
external = collections.Counter()
mailto = collections.Counter()
counts = collections.Counter()

DYN = re.compile(r'\.(svc|direct|sdirect|external)(\?|$|;)', re.I)

def refs_from(path):
    html = open(path, encoding="utf-8", errors="ignore").read()
    soup = BeautifulSoup(html, "lxml")
    out = []
    for tag, attr in (("a", "href"), ("link", "href"), ("area", "href"),
                      ("script", "src"), ("img", "src"), ("form", "action"),
                      ("iframe", "src")):
        for el in soup.find_all(tag):
            v = el.get(attr)
            if v:
                out.append(v.strip())
    # CSS url(...) inside <style> and style=""
    for m in re.finditer(r'url\(([^)]+)\)', html):
        out.append(m.group(1).strip('"\' '))
    return out

def main():
    files = sorted(glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True))
    print(f"auditing {len(files)} html files")
    for path in files:
        rel = os.path.relpath(path, SITE).replace("\\", "/")
        base_dir = os.path.dirname(path)
        for ref in refs_from(path):
            counts["total_refs"] += 1
            low = ref.lower()
            if low.startswith(("http://", "https://")):
                external[ref.split("#")[0]] += 1; counts["external"] += 1; continue
            if low.startswith("mailto:"):
                mailto[ref] += 1; counts["mailto"] += 1; continue
            if low.startswith(("javascript:", "data:", "#")) or ref == "":
                counts["inpage_or_js"] += 1; continue
            if DYN.search(ref):
                dynamic[ref].append(rel); counts["dynamic_unconverted"] += 1; continue
            # internal file link — resolve, strip fragment+query
            target = urldefrag(ref)[0].split("?")[0]
            if not target:
                counts["inpage_or_js"] += 1; continue
            abspath = os.path.normpath(os.path.join(base_dir, unquote(target)))
            counts["internal"] += 1
            if not os.path.exists(abspath):
                broken[target].append(rel)

    rep = {
        "files_audited": len(files),
        "counts": dict(counts),
        "broken_internal": {k: sorted(set(v))[:8] + ([f"...+{len(set(v))-8} more"] if len(set(v))>8 else []) for k, v in sorted(broken.items())},
        "broken_internal_unique_targets": len(broken),
        "dynamic_unconverted": {k: sorted(set(v))[:5] for k, v in list(dynamic.items())[:40]},
        "dynamic_unconverted_count": len(dynamic),
        "external_urls": sorted(external),
        "mailto": sorted(mailto),
    }
    json.dump(rep, open(os.path.join(ROOT, "audit_report.json"), "w"), indent=2)
    print("\n=== BROKEN INTERNAL LINKS (unique targets):", len(broken), "===")
    for k in sorted(broken):
        v = sorted(set(broken[k]))
        print(f"  {k}   <- {len(v)} page(s), e.g. {v[:3]}")
    print("\n=== UN-CONVERTED DYNAMIC ENDPOINTS (unique):", len(dynamic), "===")
    for k in list(dynamic)[:30]:
        print(f"  {k}   <- e.g. {sorted(set(dynamic[k]))[:2]}")
    print("\n=== EXTERNAL URLs (unique):", len(external), "===")
    for u in sorted(external):
        print(f"  {u}  (x{external[u]})")
    print("\ncounts:", dict(counts))

if __name__ == "__main__":
    main()
