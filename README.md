# Evaluating LLM-Selected Test Oracles for Underspecified Natural-Language Requirements

[Read the paper](paper.pdf) | [Download the versioned replication package](https://github.com/lythean2508/Evaluating-LLM-Selected-Test-Oracles-for-Underspecified-Natural-Language-Requirements/releases/tag/v1.0.0)

This repository contains the manuscript and frozen evidence for a diagnostic pilot of requirement-supported assertion selection. Model selection, deterministic text rules, and their intersection are compared. It is not a full end-to-end test generation benchmark.

This package accompanies the reviewer-revised manuscript on conservative assertion selection from underspecified natural-language requirements. The revision date is 20 November 2026.

## Recompute the saved results

Use Python 3.12 or later. Keep these files together in one directory.

- `verify_paper_results.py`
- `replication-controlled-pilot.zip`
- `replication-restestbench-pilot.zip`

Open a terminal in that directory and run the following command.

```text
python verify_paper_results.py score
```

On Windows with a configured Python launcher, the command can also be written as follows.

```powershell
py -3.12 .\verify_paper_results.py score
```

The verifier extracts the archives into a temporary directory, reruns their scoring programs, and compares the recomputed summaries with the frozen summaries. Expected output includes 58/126, 0/126, 29/126, and 42/42 for the controlled study and all six rows of the API results table. The final PASS message confirms a successful replay. The script prints the replay location for inspection.

The numeric observations and model responses come from the original pilot runs. The revised manuscript adds interpretation and a future evaluation protocol. A larger-model comparison and independent human annotation remain proposed work.

## Live API example

The `live` mode additionally requires Docker Desktop with a running Linux Engine, the full frozen RESTestBench checkout, the API observation scripts, a Python environment with their dependencies, and the prepared backend and PostgreSQL images. The two small data archives provide the evidence needed for rescoring.

The verifier searches for the existing experiment workspace in a `work` directory beside the script, a `work` directory beside the script's parent, or beside the Python virtual environment. The workspace must contain `restest-extension/observe.py` and the frozen `RESTestBench/services/fastapi/working/docker-compose.codex.yml` configuration. With that workspace and environment configured, run `python verify_paper_results.py live`.

The example should return HTTP 400 with `Not enough permissions` on the original service and HTTP 400 with `Item not found` on the message-changing mutant. The precise oracle's FAIL on the mutant is the expected fault-detection event.

## Manuscript source

Open `paper.tex` with XeLaTeX and the ACM `acmart` class. Keep `api-rates.pdf` beside the source. Compile twice to resolve citations and cross-references. The reference list is embedded in the source. `references.bib` provides a separate reusable bibliography.

The figure was generated from the frozen API summary. The manuscript contains 33 bibliography entries with visible DOI links or source URLs. `references.json` retains the checked source metadata. `audit.json` records the pilot counts, the benchmark commit, the data hashes, and the English-named verifier hash. The two English-named archives have the same bytes as their original counterparts.

The archive-internal README files and data records retain their original provenance. Authors should review the scientific interpretation, annotations, and submission-specific formatting before publication.

## Scope and interpretation

The controlled pilot contains 12 complete/incomplete requirement pairs, seven probes, and 144 model completions. The API pilot contains six precise/vague pairs, 17 mutants, 36 completions, and 23 recorded API observations. The model is Qwen2.5-0.5B-Instruct (Q4_K_M), with seeds 11, 23, and 47. Repeated scoring across seeds does not create additional independent mutants.

On vague API requirements, filtering changes supported coverage from 28/48 to 17/48, unsupported selections from 56/84 to 0/17, and qualified mutant detections from 0/51 to 19/51. Rules alone yield 10/17 qualified detections in one deterministic pass. These are pilot measurements, limited by one small model, sample-informed rules, one annotation set, and fixed assertion menus.

The score command replays saved evidence; it does not call an LLM or rerun services. A successful replay demonstrates numerical consistency with the stored records, not independent validation of the annotations or generalization to other systems.

## Contents and third-party material

`SHA256SUMS.txt` identifies the release files. The two data archives preserve their original bytes and internal provenance. See `THIRD_PARTY_NOTICES.md` for upstream licensing. No new license for the authors' original work is granted by this repository.
