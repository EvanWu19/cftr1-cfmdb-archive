# CFTR1 / CFMDB — Preservation Archive

An exact preservation archive of the **Cystic Fibrosis Mutation Database
(CFMDB, commonly "CFTR1")**, originally hosted at
<http://www.genet.sickkids.on.ca/> by The Hospital for Sick Children
(SickKids), Toronto. The original site is a dynamic web application scheduled
for retirement; this repository captures it so the mutation records — and their
submitted phenotypes, contributor attributions, and literature linkages — remain
available to the cystic fibrosis research community.

- **Original site last updated:** 25 April 2011
- **Captured:** 1 July 2026
- **Contents:** 18 static pages, all site assets (CSS/JS/images/downloads), and
  **2,120 mutation records** (the complete set; record IDs `sp=1 … 2239`, with
  gaps where IDs were never assigned or removed upstream)
- **Integrity:** every fetched file is logged in [`manifest.jsonl`](manifest.jsonl)
  with its URL, HTTP status, byte size, and SHA-256 checksum. Crawl totals are in
  [`crawl_summary.json`](crawl_summary.json). No fetch errors occurred.

## What this archive is — and is not

This is a **faithful copy**, not a re-interpretation. No content has been added,
summarised, reformatted, or editorialised. There are no injected banners, no
replacement search interface, and no derived datasets.

## Layout

| Path | What it is |
|------|-----------|
| [`raw/`](raw/) | The **canonical capture**: server responses stored byte-for-byte, exactly as delivered. Mutation pages are under `raw/mutations/sp-<ID>.html`. |
| [`site/`](site/) | A **browsable offline mirror** of the same content. The *only* difference from `raw/` is the mechanical link conversion every website archiver applies so the pages resolve as local files (see below). Page text, data, and markup are otherwise identical. |
| [`tools/crawl.py`](tools/crawl.py) | The crawler used to capture the site (for provenance / reproducibility). |
| [`tools/make_mirror.py`](tools/make_mirror.py) | Rebuilds `site/` from `raw/` by applying the link conversion. |
| `manifest.jsonl`, `crawl_summary.json` | Capture log and integrity record. |
| `NOTICE.md`, `LICENSE` | Attribution and licensing. |

### The only modification in `site/`

To make the exact pages navigable offline, `site/` applies these purely
mechanical rewrites (identical in spirit to `wget --convert-links` / HTTrack):

- dynamic detail links `MutationDetailPage.external?sp=N` → `mutations/sp-N.html`
- server-absolute asset paths `/include`, `/assets`, `/image` → page-relative
- the root link `/Home.html` → page-relative `Home.html`

Nothing else is changed. The original server-side search forms are preserved
verbatim but are inert offline, because their Tapestry backend no longer exists —
this is the genuine state of an archived dynamic site, not something altered.

## How to browse

- **Locally:** open [`site/Home.html`](site/Home.html) in any browser.
- **Hosted (GitHub Pages):** the entry point is `Home.html` at the Pages URL for
  this repository.

## Attribution

All scientific content remains the intellectual property of its original authors
and SickKids. This archive claims no ownership and reproduces the content
unmodified for preservation and research. See [`NOTICE.md`](NOTICE.md). Rights
holders with questions may open an issue.
