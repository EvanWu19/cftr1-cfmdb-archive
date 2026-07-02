# CFTR1 / CFMDB — Preservation Archive (with working search)

A preservation archive of the **Cystic Fibrosis Mutation Database (CFMDB,
commonly "CFTR1")**, originally hosted at <http://www.genet.sickkids.on.ca/> by
The Hospital for Sick Children (SickKids), Toronto. The original is a dynamic
web application scheduled for retirement. This repository captures it so the
mutation records — and their submitted phenotypes, contributor attributions and
literature linkages — remain available, **and re-creates the site's interactive
functions** (text search, graphic search) which otherwise die with the server.

- **Original site last updated:** 25 April 2011
- **Captured:** 1 July 2026
- **Contents:** all 18 static pages, all assets, **2,120 mutation records**
  (complete set; IDs `sp=1 … 2239` with gaps where IDs were unused), the full
  **Graphic Search** (overview map + 55 exon/intron drill-down pages + images),
  and a search index.
- **Integrity:** every statically-fetched file is logged in
  [`manifest.jsonl`](manifest.jsonl) with URL, status, size and SHA-256.

## Two layers: exact capture + working reconstruction

| Path | What it is |
|------|-----------|
| [`raw/`](raw/) | **Canonical capture** — server responses stored byte-for-byte. Detail pages under `raw/mutations/`, and the dynamic Graphic-Search pages + rendered images + search-result captures under `raw/dynamic/`. |
| [`site/`](site/) | **Functional static reconstruction** served via GitHub Pages. Same pages as the original, with the interactive functions made to work again (see below). |
| [`site_src/cfmdb_search.js`](site_src/cfmdb_search.js) | The client-side search engine injected into the search pages. |
| [`tools/`](tools/) | The capture/extract/build pipeline (provenance & reproducibility). |
| `data/`, `NOTICE.md`, `LICENSE` | Extracted index, attribution, license. |

## What works, and how it was reconstructed

The original server-side Tapestry backend no longer answers, so the functions
are reproduced client-side over an index (`site/records.json`) built from the
2,120 detail pages, enriched with data captured live before retirement.

- **Basic / Advanced / Precision / Criteria text search** — reimplemented in
  `cfmdb_search.js` with the original forms, fields, case-insensitive substring
  matching and result columns (cDNA / Protein / Legacy name, Region, Nucleotide
  Change, Consequence). E.g. searching `M470` now returns `c.1408A>G` /
  `p.Met470Val` / `M470V` (`sp-1019`).
- **Graphic Search** — the clickable gene overview and all 55 exon/intron
  drill-down pages were captured from the live server (they are GET pages); their
  images are cached locally and every image-map / mutation link rewritten to
  static files, so click-through navigation works exactly as before.
- **All internal links** (nav, detail pages, cross-references) are rewritten to
  resolve as static files.

### Fidelity notes (what is captured vs derived)

- **Region, Nucleotide Change, Consequence** are harvested from the live search
  backend for 1,635 / 2,120 records (the backend's text search caps coverage);
  the remainder show those two columns blank but are fully searchable by name /
  phenotype and have complete detail pages.
- **Mutation type** (structural: Substitution/Deletion/… and functional:
  Missense/Nonsense/…), used by the Criteria/Advanced type filters, is **derived
  from HGVS nomenclature**, because the database's own type field is not present
  on any capturable page. It is an interpretation, not the original DB value.

## How to browse

- **Hosted:** <https://evanwu19.github.io/cftr1-cfmdb-archive/site/Home.html>
- **Search:** <https://evanwu19.github.io/cftr1-cfmdb-archive/site/SearchPage.html>
- **Graphic Search:** <https://evanwu19.github.io/cftr1-cfmdb-archive/site/PicturePage.html>
- **Locally:** open [`site/Home.html`](site/Home.html) (search needs to be served
  over http — use the hosted link or a local web server, as browsers block
  `fetch` of `records.json` from `file://`).

## Attribution

All scientific content remains the intellectual property of its original authors
and SickKids; this archive claims no ownership and reproduces it for preservation
and research. See [`NOTICE.md`](NOTICE.md). Rights holders may open an issue.
