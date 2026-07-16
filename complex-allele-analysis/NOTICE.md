# Attribution & Provenance — Complex-Allele Analysis

This folder is a **derived, computational analysis** built on top of the CFTR1/
CFMDB preservation archive in this repository. It identifies complex alleles by
reading each variant's submitted *Other Details* and *Phenotype* text.

## Sources

- **CFTR1 / CFMDB** — the variant records, *Other Details* and *Submitted
  Phenotype Details* that were screened are the intellectual property of **The
  Hospital for Sick Children (SickKids), Toronto** and the contributing
  investigators, as described in the repository-root [`../NOTICE.md`](../NOTICE.md).
  This analysis reproduces short quoted snippets of that text (the *Text referring
  to* column) for evidentiary purposes only.

- **CFTR2** — partner-variant resolution and the optional *CFTR2 determination*
  column use cross-references (legacy name ↔ protein ↔ cDNA ↔ alternative names,
  and clinical determination) from the **CFTR2 project** variant list
  (<https://cftr2.org>), a resource of the US CF Foundation, Johns Hopkins
  University, and The Hospital for Sick Children. The CFTR2 data is © the CFTR2
  project and is used here for research/educational purposes with attribution.
  - The **raw CFTR2 spreadsheet is not redistributed** in this repository. To
    reproduce `intermediate/alias_index.json` and `intermediate/cftr2.json`,
    download the current variant list from <https://cftr2.org> and pass it to
    `scripts/01_build_index_and_screen.py --cftr2 <file>`.
  - `intermediate/alias_index.json` and `intermediate/cftr2.json` are **derived
    lookup subsets** (identifier cross-references and per-variant determination)
    included only to make the analysis reproducible without re-downloading CFTR2.

## License

The **analysis code** in `scripts/` (Python and the AI-workflow JavaScript) is
released under the **MIT License**, consistent with the tooling in this
repository's [`../tools/`](../tools/) — see [`../LICENSE`](../LICENSE).

The **derived results** in `results/` and `intermediate/` combine CFTR1 content
(© SickKids and contributors) with CFTR2 cross-references (© the CFTR2 project).
No ownership is claimed over that underlying scientific content.

## Not clinical advice

This is a computational screen provided for research use. It is **not** a clinical
or diagnostic determination. Any specific complex-allele call should be verified
against the primary literature cited in the corresponding CFTR1 record before use.

If you are a rights holder and have questions, please open an issue on this
repository.
