# CFTR1 Complex-Allele Screen

A systematic screen of all **2,121** variants in this CFTR1/CFMDB archive for
**complex alleles** — variants reported to occur **in cis** (on the same
chromosome / same allele) with one or more other CFTR variants — by reading each
variant's *Other Details* and *Submitted Phenotype Details*.

## Results

| Determination | Count |
|---|---|
| **Yes** — confirmed complex allele (cis partner stated) | **79** |
| **Uncertain** — a second variant co-occurs but phase (cis/trans) is not stated | **84** |
| No | 1,958 |
| **Total screened** | **2,121** |

Main deliverable: [`results/CFTR1_complex_allele_screen.xlsx`](results/CFTR1_complex_allele_screen.xlsx)
— two sheets, **Complex allele hits** (the 163 Yes+Uncertain rows) and **All 2121
screened**. Yes rows are shaded green, Uncertain amber. The same data is also in
CSV and JSON under [`results/`](results/).

Of the 79 confirmed complex alleles, 67 have every cis partner resolved to a
modern cDNA name; the remaining 12 keep at least one partner in its raw legacy
form (shown in `[square brackets]`) because that partner is not catalogued as a
separate entry in CFTR1 or CFTR2 (e.g. certain legacy nucleotide names, or
poly-T/TG tract alleles).

Calibration example: **c.3600A>G** → complex allele **`c.3600A>G;c.3659C>T`**
(the *Other Details* say "found together with K1220E on the same non-ΔF508 CF
chromosome"; the phenotype says "in cis with 3791C/T (K1220E)", and 3791C/T =
c.3659C>T).

## What counts as a complex allele

The primary variant **plus** one or more other CFTR variants **on the same
chromosome / same allele / in cis**. A variant on the *other* allele (in *trans*
— the usual compound-heterozygous partner, e.g. a ΔF508 "on the other
chromosome") is **not** part of the complex allele; where the source stated such
a trans partner it is recorded separately in the *Trans partner* column. A
co-occurring variant whose phase the text never states (e.g. "in association
with", "in conjunction with") is classified **Uncertain**, not Yes.

## Method

1. **Keyword screen (deterministic).** All 2,121 variants' *Other Details* +
   *Submitted Phenotype Details* were scanned for ~25 complex-allele cues
   ("complex allele", "in cis", "same allele/chromosome", "together with", "also
   carries", "haplotype", "and <MUT>", "second mutation", …) → **372 candidates**.
2. **AI judgement, pass 1 (candidates).** 31 agents classified the 372 candidates
   (Yes/Uncertain/No) and extracted the keyword, the exact referring text, the
   reasoning, and the partner variant token(s).
3. **AI judgement, pass 2 (safety net).** Because a complex allele can be
   described without any keyword, 81 agents read the remaining **1,618**
   non-keyword variants that still had text — surfacing **55 additional hits**.
   The 131 variants with no text were auto-classified "No".
4. **Cis-partner correction, pass 3.** 12 agents re-examined all 163 hits to
   separate genuine **cis** partners from **trans** partners, reaffirm/correct
   the verdict, and express each cis partner in a resolvable form.
5. **Partner resolution (deterministic).** Each cis partner was resolved to a
   cDNA name via a combined CFTR1+CFTR2 alias index (cDNA, legacy nucleotide
   names with `C/T`→`C>T` normalization, protein one/three-letter forms,
   `*`/`Ter`→`X`, alternative names). Notation-equivalent forms are collapsed;
   genuinely ambiguous tokens are left as raw bracketed text rather than guessed.
6. **Verification.** Two independent AI audits on stratified samples returned
   43/44 and 33/34 agreement (~97%); every issue they raised was fixed.

See the three AI orchestration scripts in
[`scripts/workflows/`](scripts/workflows/) for the exact agent prompts and
schemas used in passes 1–3.

## Column guide (results table)

- **Variant (cDNA name)** — CFTR1 primary variant (HGVS cDNA).
- **Protein Name / Legacy name** — as in CFTR1.
- **Nucleotide change** — the cDNA change without the `c.` prefix (derived).
- **Consequence** — variant class (missense/nonsense/frameshift/splicing/…),
  derived from the protein and cDNA notation.
- **Key Word** — the phrase in the source that signals the relationship.
- **Text referring to** — the exact clause from *Other Details* or *Submitted
  Phenotype Details*.
- **Complex allele found or not** — Yes / Uncertain / No.
- **Your judgement reason** — the AI's reasoning.
- **Complex allele cDNA name** — combined allele, primary first, cis partners
  appended (e.g. `c.3600A>G;c.3659C>T`). `[brackets]` = partner not resolvable to
  a catalogued cDNA, shown raw.
- **Trans partner (not part of complex allele)** — co-occurring variant(s)
  explicitly on the *other* allele (audit trail; excluded from the complex allele).
- **Confidence / Partner tokens (raw) / Screen source / CFTR2 determination /
  sp_id / source_url** — provenance and supporting detail.

## Reproduce

```
cd scripts
# Step 1 — build the alias index + keyword screen + AI-judgement batches.
#   Needs the CFTR2 variant xlsx (not redistributed here; get it from cftr2.org).
python 01_build_index_and_screen.py --cftr2 /path/to/CFTR2_<date>.xlsx

# Step 2 — the AI judgement passes (workflows/pass1..3) were run with an agent
#   orchestrator over the batches from step 1; their structured outputs are saved
#   as intermediate/judgements_pass{1,2,3}.json (committed here).

# Step 3 — assemble the final table from the judgements (runs standalone from the
#   committed judgements + this repo's data/mutations.json + the alias index).
python 02_resolve_and_assemble.py
```

`02_resolve_and_assemble.py` reproduces `results/` field-for-field from the
committed judgements. Requires `openpyxl` (`pip install openpyxl`).

## Folder layout

```
complex-allele-analysis/
├── README.md                     this file
├── NOTICE.md                     attribution (CFTR1, CFTR2) + license
├── results/                      final table (xlsx, csv, json)
├── scripts/                      pipeline (python + AI-workflow js) + lib_resolver
└── intermediate/                 alias index, keyword candidates, AI judgements, cftr2 subset
```

## Caveats

- **Uncertain ≠ negative.** 84 variants co-occur with another variant whose phase
  the source never states; many are plausible complex alleles worth manual review.
- **Old amino-acid numbering.** Some source text uses historical protein numbering
  (e.g. "K1220E" for today's T1220I / c.3659C>T); resolution used the legacy
  nucleotide name where available.
- **Poly-T / TG tracts** (5T, (TG)mTn) stated in cis are counted as cis partners
  in their tract notation.
- A few **borderline calls** exist (e.g. a near-reference (TG)12T7 background; one
  record whose primary cDNA and free-text protein name disagree at codon 437);
  these are flagged in the reasoning and left conservative.

*This analysis is derived, computational, and provided for research use; it is not
a clinical determination. Verify any specific complex allele against the primary
literature before use.*
