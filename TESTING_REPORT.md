# CFTR1 / CFMDB Archive — Full Link & Function Test Report

**Date:** 8 July 2026
**Scope:** every internal link and every interactive function of the reconstructed
site (`site/`), tested exhaustively; easy issues fixed, deeper issues reported.

## Method

- **Static link audit** (`tools/audit_links.py`): parsed all **2,418** files and
  every `href` / `src` / `<area>` / `<form action>` / CSS `url()` — **87,727
  references**, resolving each internal target to a real local file.
- **Function tests**: verified each search form's required DOM element IDs exist
  and the search engine (`cfmdb_search.js`) is wired in; then ran the exact
  match logic of all four search modes against the live index (`records.json`,
  2,121 records) with representative queries.
- **Graphic search**: verified the overview map, all 55 region drill-down pages,
  their 56 images, and mutation click-through links resolve.
- Live re-confirmation in a browser was attempted but the Chrome extension was
  disconnected this session; the headless checks above stand in for it.

## Result summary

| | Before this pass | After |
|---|---|---|
| Unique broken internal links | **118** | **46** (all unfixable-at-source — see below) |
| Un-converted dead dynamic endpoints | 7 | **0** |
| Mutation records in archive | 2,120 | **2,121** (recovered `sp=0`) |
| Sub-resources captured | — | **+120** (newsletters, consortium tables, images, JS libs, FASTA) |

Every broken link that *could* be fixed was fixed. The 46 that remain are all
either dead on the original server too, or require the retired dynamic backend.

## Fixes applied

1. **Sub-directory link bug (highest impact).** Detail pages (`mutations/`) and
   graphic pages (`picture/`) referenced root-level pages/logos/downloads
   *relatively* (`SearchPage.html`, `image/mutationlogo.gif`, `download/…`), so
   they 404-ed from those sub-folders. **The entire top navigation, header logos
   and mini-search box were broken on all 2,121 detail pages + 55 graphic
   pages.** Fixed by depth-correct `../` prefixing in the build.
2. **120 missing sub-resources fetched** from the still-live server and wired in:
   - **67 CF Consortium newsletters** (`resource/nl/`) — a substantial content
     archive that `NewsLetters.html` links to, previously entirely 404.
   - **Consortium data tables & figures** (`resource/`, `resource/old/`,
     `cftr/freqtables.html`) with their **49 images** and notes pages.
   - `CFTR.fasta` (full CFTR genomic sequence), `image/cf_domain.jpg`,
     `include/overlib.js`, `dojo3.js`, Tapestry `DatePicker.js`/icon,
     `cftr2ComingSoon.html`.
3. **Recovered `sp=0`** — a real record (`c.-887C>T`, the most-upstream promoter
   variant) that the original crawl skipped by starting at `sp=1`. Added to the
   archive and the search index.
4. **Dead form POSTs neutralised** (7 Tapestry endpoints) so submitting a form no
   longer 404s; **stale `jsessionid` link fragments stripped.**
5. **Search: delta-symbol normalisation** — `ΔF508`, `[delta]F508` and
   `deltaF508` now all match the same records (previously only `[delta]F508` /
   `F508` did).

## Function-by-function results

| Function | Status | Notes |
|---|---|---|
| Top navigation (all pages) | ✅ Fixed | was broken on every sub-folder page |
| Basic Text Search | ✅ Works | all 10 field options; verified across many queries |
| Advanced Text Search | ✅ Works | field terms, region, type, year, institute, AND/OR |
| Precision Search | ✅ Works | correct field mapping |
| Criteria Search | ✅ Works | structural type + coding/non-coding region |
| Graphic Search (overview→region→variant) | ✅ Works | images + click-through resolve |
| Mutation detail pages | ✅ Works | nav, logos, PubMed link |
| Newsletters / Consortium data | ✅ Now works | were 404, now captured |
| Genomic / mRNA / polypeptide **sequence viewers** | ⚠️ Non-functional | interactive; needs dead backend — see below |
| Submit-a-mutation form | ⚠️ Inert (by design) | cannot submit to a retired database |

## Remaining issues

### A. Dead on the original server too (preserved faithfully, not fixable)
- **40 newsletter images** (`CFnewslet.*.gif`) — already return 404 on the live
  server; the newsletters are text-only at source.
- **1 legacy CGI** (`/cftr-cgi-bin/sidestring`, image generator) referenced by a
  1999 consortium table — 404 on the live server.

### B. Requires the retired dynamic backend (data preserved where possible)
- **Sequence viewers** (`GenomicDnaSequencePage`, `MRnaPolypeptideSequencePage`):
  the pages render, but their "click a region / enter positions → show 2,000 nt"
  feature fetched data live from endpoints that now return **empty** on GET
  (`cftrdnasequence*.txt`, `polypeptideSequence/*.txt`). The interactive slicer
  is not reproduced. **Mitigation:** the complete CFTR genomic sequence is
  preserved in [`CFTR.fasta`](CFTR.fasta) (192 kB).
- **Submit form**: intentionally inert — a preservation archive cannot accept new
  submissions.

### C. Data-derivation limits (also covered in README)
- **`sp=1873`** is referenced by graphic region page `domain_8` but the record is
  **empty on the original server** — a source-side inconsistency; no record
  exists to link to.
- **Mutation-type filters** are HGVS-derived (the DB's own type field is not on
  any capturable page). Two dropdown options — **"Large In/del"** and
  **"Promoter"** — are never produced by the derivation, so filtering by those
  two returns nothing.
- **`term=null` PubMed links on 477 detail pages** — faithful to the original:
  the server wrote `term=null` for variants with no legacy/protein name, so the
  "check PubMed" link is unhelpful for those records.
- **Nucleotide Change / Consequence** columns are blank for the records the live
  search backend never returned (coverage 1,636 / 2,121) — see README.
- **No relevance ranking**: results are returned in record-ID order (as a
  substring filter), so an exact-name match can appear below records that merely
  mention the name in their phenotype/notes text.

### D. Search naming nuance
- The index stores the **database's own variant names** (legacy `[delta]F508`,
  HGVS `p.Phe508del`). F508del is found by `F508`, `ΔF508`, `[delta]F508`,
  `deltaF508`, `508del`, `Phe508del`, or `c.1521…` — but **not** by the compact
  string `F508del` typed literally, because that exact substring is in no stored
  field. (A nomenclature-normalisation layer could be added on request.)
