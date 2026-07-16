# Scripts — CFTR1 complex-allele pipeline

Run order: **01 → workflows (pass 1,2,3) → 02**.

| File | Role |
|---|---|
| `01_build_index_and_screen.py` | Build the CFTR1+CFTR2 alias index; derive Nucleotide-change/Consequence; keyword-screen all 2,121 variants; write AI-judgement batches. Needs the CFTR2 xlsx (`--cftr2`, or `CFTR2_XLSX` env). |
| `workflows/pass1_keyword_judgement.workflow.js` | AI pass 1 — classify the 372 keyword candidates; extract keyword, referring text, reasoning, partner tokens. |
| `workflows/pass2_nonkeyword_judgement.workflow.js` | AI pass 2 — read the 1,618 non-keyword-but-has-text variants to catch complex alleles that use no keyword. |
| `workflows/pass3_cis_partner_correction.workflow.js` | AI pass 3 — re-examine the 163 hits; separate cis from trans partners; reaffirm/correct verdicts. |
| `02_resolve_and_assemble.py` | Resolve cis partners to cDNA, assemble combos (primary first), enforce reciprocity, write `results/`. Runs standalone from the committed judgements. |
| `lib_resolver.py` | Partner-token → canonical cDNA resolver (shared). |

## Notes

- The `*.workflow.js` files are the exact agent-orchestration scripts (prompts +
  JSON output schemas) used to produce `intermediate/judgements_pass{1,2,3}.json`.
  They were executed by an agent orchestrator (fan-out of one agent per batch),
  not by Node; they are included as an exact record of the AI method. The
  structured outputs they produced are committed, so `02` reproduces the results
  without re-running any agents.
- Python deps: standard library + `openpyxl` (`pip install openpyxl`).
- Paths are resolved relative to each script's location; run from anywhere.
