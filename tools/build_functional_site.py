#!/usr/bin/env python3
"""
Assemble a FUNCTIONAL static archive under site/ :

  * all static info pages + all mutation detail pages (link-converted)
  * the four search pages made to actually work, by injecting cfmdb_search.js
    (client-side reimplementation) and neutralising the dead Tapestry POST
  * the Graphic Search made to work: the overview map + every region drill-down
    page captured from the live server, with their images cached locally and all
    image-map / mutation links rewritten to static files
  * records.json — the search index (extracted detail-page data merged with the
    live-harvested Region / Nucleotide Change / Consequence, plus HGVS-derived
    structural & functional mutation type for the type filters)

Inputs: raw/, raw/dynamic/ (from capture_dynamic.py), data/mutations.json
        (from extract_full.py), data/harvest.json, site_src/cfmdb_search.js
"""
import glob, html as H, json, os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
DYN = os.path.join(RAW, "dynamic")
SITE = os.path.join(ROOT, "site")
DATA = os.path.join(ROOT, "data")
SRC = os.path.join(ROOT, "site_src")

SEARCH_PAGES = {"SearchPage.html", "AdvancedSearchPage.html", "MutationSearch.html"}

# root-level targets that, when referenced *relatively* from a sub-directory page,
# must be prefixed with the correct number of "../" so they resolve.
ROOT_HTML = {os.path.basename(p) for p in glob.glob(os.path.join(RAW, "*.html"))}
ROOT_DIRS = ("image/", "include/", "assets/", "download/", "resource/",
             "cftr/", "cftrdnasequence/", "polypeptideSequence/")
ROOT_FILES = {"CFTR.fasta"}


def prefix_relative_root_links(html, root):
    """For sub-directory pages (root != ''), prefix links that point at
    root-level pages / dirs / files. Same-directory siblings (e.g. picture
    domain_*.html, img/*) and absolute / external / anchor links are left alone."""
    if not root:
        return html

    def repl(m):
        attr, q, val = m.group(1), m.group(2), m.group(3)
        head = val.split("?")[0].split("#")[0]
        if val.startswith(("http://", "https://", "mailto:", "javascript:",
                           "data:", "#", "/", "../", root)):
            return m.group(0)
        if head in ROOT_HTML or head in ROOT_FILES or head.startswith(ROOT_DIRS):
            return f'{attr}={q}{root}{val}{q}'
        return m.group(0)

    return re.sub(r'(href|src|action)=(["\'])([^"\']*)\2', repl, html)


def svc_local(url):
    """Local filename for a *.svc image (captured PNGs), served with .png so the
    browser gets image/png. Mirrors capture_dynamic.svc_name but with .png."""
    m = re.search(r"/([^/?]+\.svc)\?(.*)$", H.unescape(url))
    if not m:
        return re.sub(r"[^A-Za-z0-9.]", "_", H.unescape(url)) + ".png"
    return m.group(1) + "__" + re.sub(r"[^A-Za-z0-9]", "_", m.group(2)) + ".png"


# ---------- link conversion ----------
def convert_common(html, root):
    # dead Tapestry session ids in links -> drop
    html = re.sub(r';jsessionid=[A-Za-z0-9]+', '', html)
    # dynamic detail links -> static files
    html = re.sub(r'/?MutationDetailPage\.external\?sp=(\d+)',
                  lambda m: root + "mutations/sp-" + m.group(1) + ".html", html)
    # server-absolute asset/resource dirs -> root-relative
    for d in ("include", "assets", "image", "download", "resource", "cftr",
              "cftrdnasequence", "polypeptideSequence"):
        html = html.replace('"/' + d + '/', '"' + root + d + '/').replace("'/" + d + "/", "'" + root + d + "/")
    # server-absolute root pages -> root-relative (e.g. /Home.html)
    html = re.sub(r'(href|src)="/([A-Za-z][A-Za-z0-9]*\.html)"',
                  lambda m: m.group(1) + '="' + root + m.group(2) + '"', html)
    # dead Tapestry form POST endpoints -> inert (avoid 404 on submit)
    html = re.sub(r'action="/[^"]*\.s?direct[^"]*"', 'action="#"', html)
    # remaining relative links to root-level targets -> add ../ depth
    html = prefix_relative_root_links(html, root)
    return html


def convert_graphic(html, root, img_root, domain_root):
    """Rewrite *.svc images -> cached files, domain_id links -> static files."""
    html = re.sub(r'(?:/)?PicturePage\.html\?domain_id=([A-Za-z0-9]+)',
                  lambda m: domain_root + "domain_" + m.group(1) + ".html", html)
    html = re.sub(r'([^"\']*\.svc(?:\?[^"\']*)?)',
                  lambda m: img_root + svc_local(m.group(1)) if ".svc" in m.group(1) else m.group(1), html)
    html = convert_common(html, root)
    # bare Graphic-Search overview link back to root PicturePage
    html = html.replace(domain_root + "domain_.html", root + "PicturePage.html")
    return html


def inject_search(html, root):
    html = re.sub(r'action="/[^"]*\.s?direct[^"]*"', 'action="#"', html)
    tag = '<script src="' + root + 'cfmdb_search.js"></script>'
    m = re.search(r'</body>', html, re.I)
    return html[:m.start()] + tag + html[m.start():] if m else html + tag


# ---------- mutation type derivation (fallback when DB field not capturable) ----------
def struct_type(cdna):
    c = (cdna or "").lower()
    if "delins" in c: return "Insertion/deletion"
    if "dup" in c: return "Duplication"
    if "del" in c and "ins" in c: return "Insertion/deletion"
    if "del" in c: return "Deletion"
    if "ins" in c: return "Insertion"
    if "inv" in c: return "Inversion"
    if re.search(r"\(?[acgt]{1,3}\)?\d*\[", c) or "[" in c: return "Microsatellite"
    if ">" in c: return "Substitution"
    return ""


def func_type(rec):
    p = (rec.get("protein_name") or "").lower()
    c = (rec.get("cdna_name") or "").lower()
    reg = (rec.get("region") or "").lower()
    lreg = (rec.get("legacy_region") or "").lower()
    name = ((rec.get("legacy_name") or "") + " " + (rec.get("cdna_name") or "")).lower()
    # Promoter — region is authoritative; check before the splice rule because
    # promoter cDNA positions (c.-887 …) otherwise look like splice positions.
    if "promoter" in reg or "promoter" in lreg:
        return "Promoter"
    # Large In/del — gross rearrangements: whole-exon / multi-exon deletions,
    # kb-scale deletions, uncertain-boundary notation c.(?_x)_(y_?)del.
    if ("(?_" in c or "cftrdele" in name or "delex" in name or "del ex" in name
            or " - " in reg
            or ("kb" in c and ("del" in c or "ins" in c or "dup" in c))):
        return "Large In/del"
    if "ter" in p or p.endswith("*") or re.search(r"\*\d*$", p): return "Nonsense"
    if "fs" in p: return "Frame Shift"
    if "intron" in reg or re.search(r"[+\-]\d", c): return "Splicing"
    if "del" in c or "ins" in c or "dup" in c:
        return "In frame" if re.search(r"del|dup|ins", c) and "fs" not in p else "Frame Shift"
    if re.search(r"p\.[a-z]{3}\d+[a-z]{3}", p): return "Missense"
    return "Sequence Variation"


def build_records():
    recs = json.load(open(os.path.join(DATA, "mutations.json"), encoding="utf-8"))
    harvest = {}
    hp = os.path.join(DATA, "harvest.json")
    if os.path.exists(hp):
        for r in json.load(open(hp, encoding="utf-8")).get("rows", []):
            harvest[r["sp_id"]] = r
    for r in recs:
        h = harvest.get(r["sp_id"], {})
        r["nucleotide_change"] = h.get("nucleotide_change", "")
        r["consequence"] = h.get("consequence", "")
        if h.get("region") and not r.get("region"):
            r["region"] = h["region"]
        r["struct_type"] = struct_type(r.get("cdna_name"))
        r["func_type"] = func_type(r)
    json.dump(recs, open(os.path.join(SITE, "records.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    return len(recs), sum(1 for r in recs if r["nucleotide_change"])


def main():
    if os.path.exists(SITE):
        shutil.rmtree(SITE)
    os.makedirs(SITE)
    for sub in ("include", "assets", "image", "download", "resource", "cftr"):
        if os.path.isdir(os.path.join(RAW, sub)):
            shutil.copytree(os.path.join(RAW, sub), os.path.join(SITE, sub), dirs_exist_ok=True)
    # root-level non-html assets (e.g. CFTR.fasta) copied verbatim
    for f in ("CFTR.fasta",):
        if os.path.isfile(os.path.join(RAW, f)):
            shutil.copy(os.path.join(RAW, f), os.path.join(SITE, f))
    if os.path.isdir(os.path.join(RAW, "sequence")):
        shutil.copytree(os.path.join(RAW, "sequence"), os.path.join(SITE, "sequence"), dirs_exist_ok=True)
    # some copied resource/cftr pages are full CFMDB templates (nav + css):
    # convert their links with the correct sub-directory depth
    for sub in ("resource", "cftr"):
        for p in glob.glob(os.path.join(SITE, sub, "**", "*.html"), recursive=True):
            rel = os.path.relpath(p, SITE).replace("\\", "/")
            depth = rel.count("/")            # dirs between site root and file
            html = open(p, encoding="utf-8", errors="ignore").read()
            open(p, "w", encoding="utf-8").write(convert_common(html, "../" * depth))
    shutil.copy(os.path.join(SRC, "cfmdb_search.js"), os.path.join(SITE, "cfmdb_search.js"))
    shutil.copy(os.path.join(SRC, "cfmdb_sequence.js"), os.path.join(SITE, "cfmdb_sequence.js"))
    # landing redirect so /site/ (no explicit file) resolves to the homepage
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<title>CFTR1 / CFMDB Archive</title>'
        '<meta http-equiv="refresh" content="0; url=Home.html">'
        '<link rel="canonical" href="Home.html"></head><body>'
        '<p>Redirecting to the <a href="Home.html">CFTR1 / CFMDB archive</a>&hellip;</p>'
        '</body></html>\n')

    # static + search pages (root, depth 0)
    for p in glob.glob(os.path.join(RAW, "*.html")):
        name = os.path.basename(p)
        html = open(p, encoding="utf-8", errors="ignore").read()
        if name == "PicturePage.html":
            html = convert_graphic(html, "", "picture/img/", "picture/")
        else:
            html = convert_common(html, "")
        if name in SEARCH_PAGES:
            html = inject_search(html, "")
        if name in ("GenomicDnaSequencePage.html", "MRnaPolypeptideSequencePage.html"):
            tag = '<script src="cfmdb_sequence.js"></script>'
            m = re.search(r'</body>', html, re.I)
            html = html[:m.start()] + tag + html[m.start():] if m else html + tag
        open(os.path.join(SITE, name), "w", encoding="utf-8").write(html)

    # mutation detail pages (depth 1)
    os.makedirs(os.path.join(SITE, "mutations"), exist_ok=True)
    nmut = 0
    for p in glob.glob(os.path.join(RAW, "mutations", "sp-*.html")):
        html = convert_common(open(p, encoding="utf-8", errors="ignore").read(), "../")
        open(os.path.join(SITE, "mutations", os.path.basename(p)), "w", encoding="utf-8").write(html)
        nmut += 1

    # graphic-search region pages + cached images (depth 1 under picture/)
    os.makedirs(os.path.join(SITE, "picture", "img"), exist_ok=True)
    ndom = 0
    if os.path.isdir(DYN):
        for p in glob.glob(os.path.join(DYN, "PicturePage__domain_id_*.html")):
            did = re.search(r"domain_id_([A-Za-z0-9]+)\.html", p).group(1)
            html = convert_graphic(open(p, encoding="utf-8", errors="ignore").read(),
                                   "../", "img/", "")
            if "SEARCH" not in os.path.basename(p):
                pass
            open(os.path.join(SITE, "picture", "domain_" + did + ".html"), "w", encoding="utf-8").write(html)
            ndom += 1
        for p in glob.glob(os.path.join(DYN, "*.img")):
            dst = os.path.basename(p)[:-4] + ".png"  # captured PNGs; serve as .png
            shutil.copy(p, os.path.join(SITE, "picture", "img", dst))
        # overview image referenced by root PicturePage.html lives at picture/img/
        # (already copied above since capture saved it under raw/dynamic/*.img)

    n, nh = build_records()
    print(f"site built: {nmut} detail pages, {ndom} graphic region pages, "
          f"{n} search records ({nh} with harvested nucleotide/consequence)")


if __name__ == "__main__":
    main()
