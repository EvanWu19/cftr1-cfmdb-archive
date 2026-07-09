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
- **Contents:** all 18 static pages, all assets, **2,121 mutation records**
  (complete set; IDs `sp=0 … 2239` with gaps where IDs were unused), the full
  **Graphic Search** (overview map + 55 exon/intron drill-down pages + images),
  the **67 CF Consortium newsletters** and consortium data tables, `CFTR.fasta`
  (full CFTR genomic sequence), and a search index.
- **Integrity:** every statically-fetched file is logged in
  [`manifest.jsonl`](manifest.jsonl) with URL, status, size and SHA-256.
- **Link & function test:** see [`TESTING_REPORT.md`](TESTING_REPORT.md) — all
  87,727 references audited; every fixable broken link fixed; the 46 that remain
  are dead on the original server too or need the retired dynamic backend.

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
2,121 detail pages, enriched with data captured live before retirement.

- **Basic / Advanced / Precision / Criteria text search** — reimplemented in
  `cfmdb_search.js` with the original forms, fields, case-insensitive substring
  matching and result columns (cDNA / Protein / Legacy name, Region, Nucleotide
  Change, Consequence). E.g. searching `M470` now returns `c.1408A>G` /
  `p.Met470Val` / `M470V` (`sp-1019`).
- **Graphic Search** — the clickable gene overview and all 55 exon/intron
  drill-down pages were captured from the live server (they are GET pages); their
  images are cached locally and every image-map / mutation link rewritten to
  static files, so click-through navigation works exactly as before.
- **Sequence viewers** — both reimplemented (`cfmdb_sequence.js`) over recovered
  sequences: the **Genomic DNA** viewer over [`CFTR.fasta`](CFTR.fasta)
  (189,638 nt), and the **mRNA(cDNA) & Polypeptide** viewer over the recovered
  CFTR coding cDNA (4,443 nt) and protein (1,480 aa, one- and three-letter) under
  [`sequence/`](sequence/). Enter a start position + length, or click the ruler;
  the mRNA page switches between DNA / three-letter / one-letter.
- **All internal links** (nav, detail pages, cross-references) are rewritten to
  resolve as static files.

### Fidelity notes — exact capture vs. reconstruction

The 2,121 **detail pages** — each variant's authoritative record (cDNA / protein
/ legacy name, region, submitted phenotype, contributors, institute, reference,
PubMed link) — are captured **exactly and completely for every record**. The two
notes below concern *only the search layer*: the columns and filters that the
original site generated dynamically on the server. That backend is gone, so those
had to be reconstructed — and reconstruction cannot recover data the server never
put on a capturable page. Here is exactly where the limits are.

**1. Two search-result columns can be blank: Nucleotide Change & Consequence.**

The original search *results table* shows six columns. They do not all come from
the same place, and they do not all have the same coverage:

| Result column | Where it comes from | Populated |
|---|---|---|
| cDNA / Protein / Legacy name | The captured detail pages | complete |
| Region | The detail page's *Exon or Intron* field (captured) | 1,819 / 2,121 |
| **Nucleotide Change** | Harvested from the live search backend | 1,635 / 2,121 |
| **Consequence** | Harvested from the live search backend | 1,583 / 2,121 |

"Nucleotide Change" and "Consequence" appeared **only** in the rows the server's
search engine generated on the fly — they are never printed on a detail page. To
preserve them at all, I replayed queries against the live site before it was
retired and scraped those rows. The server's own text index only ever returned a
subset of the database in response to searches, and that is the hard ceiling on
coverage: for the ~485 records it never surfaced, these two columns are shown
**blank**. Nothing else is lost for those records — they are still fully
searchable (by cDNA / protein / legacy name, region, and phenotype text) and
their detail pages are 100% complete. Only these two supplementary columns are
affected.

**2. The mutation-*type* filters are derived from HGVS names, not the DB's own value.**

The Criteria and Advanced searches let you filter by mutation type — a
**structural** class (Substitution, Deletion, Insertion, Indel, …) and a
**functional** class (Missense, Nonsense, Frameshift, Splice, …). The original
database clearly stored such a value, because its filters used it — but that field
is **not printed on any page that can be captured**: not on the detail pages, and
not in the search-result rows. There was simply no authoritative copy of it to
preserve, so with an exact capture alone the type filters would do nothing.

To keep them working, each variant's type is instead **computed from its HGVS
name** using standard rules — e.g. `>` → substitution; `del` / `ins` / `dup` /
`delins` → the matching structural class; a protein change like `p.Met470Val` →
missense, a `Ter` / `*` change → nonsense, `fs` → frameshift, canonical splice
positions → splice; promoter-region variants → promoter; whole-exon / multi-exon
/ kb-scale rearrangements → large in/del. This classification is present for
2,119 / 2,121 (structural) and 2,121 / 2,121 (functional), and all eight
functional-type filter options return results.

This is an **interpretation from nomenclature, not the database's original
classification.** It is correct for the large majority of variants and makes the
filters usable, but for ambiguous cases the filtered set may differ from what the
original site would have returned. Importantly, this affects *only* the type
grouping used by those two filters — the variant records themselves are untouched
and exact.

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
