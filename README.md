# Evaluating LLM-Selected Test Oracles for Underspecified Natural-Language Requirements

[Manuscript source (`paper.tex`)](paper.tex) | [Compiled manuscript PDF (`paper.pdf`)](paper.pdf) | [Full replication release (v1.1.1)](https://github.com/lythean2508/Evaluating-LLM-Selected-Test-Oracles-for-Underspecified-Natural-Language-Requirements/releases/tag/v1.1.1) | [Original pilots (v1.0.0)](https://github.com/lythean2508/Evaluating-LLM-Selected-Test-Oracles-for-Underspecified-Natural-Language-Requirements/releases/tag/v1.0.0)

This repository contains the manuscript and frozen evidence for a diagnostic study of requirement-supported assertion selection under natural-language underspecification. Grammar-constrained LLM selection, deterministic lexical rules, and their agreement intersection are compared on shared execution traces. It is not a full end-to-end test generation benchmark.

Version 1.0.0 preserves the two original pilots as published on 20 November 2026. Version 1.1.1 added the paired Qwen 0.5B/7B Vulkan experiments, held-out TodoApp frozen-rule transfer, and eight-policy label sensitivity analysis. The **v1.2.0 release** (25 November 2026) preserves all frozen experimental archives byte-for-byte while harmonizing CPU vs. Vulkan reporting across Abstract/Results/Conclusion, tabulating all 144 controlled completions (including complete `exact` mutation kills and structural ambiguity breakdowns), adding unvetted compatible-kill and four-part partition tables for RQ4, analyzing cross-step scope leakage on TodoApp `DELETE`, upgrading Figure 1 to vector TikZ, and expanding the bibliography to 48 entries. The manuscript on the default branch incorporates a subsequent audit of the tables, figures, claims, and reference metadata.

- [Paired API follow-up (`followup/README.md`)](followup/README.md): Qwen2.5-0.5B-Instruct vs. Qwen2.5-7B-Instruct under Vulkan, frozen-rule transfer to four held-out TodoApp pairs, and eight-policy sensitivity replay.
- [Annotated source guide in Vietnamese (`SOURCES.md`)](SOURCES.md): maps study claims to replication files and documents all 48 verified references.
- [Comparison with closest work (`RELATED-WORK.md`)](RELATED-WORK.md): contrasts selective assertion gating with closest 2024–2026 oracle, abstention, and requirements-gating studies.
- [Validation record (`VALIDATION.md`)](VALIDATION.md): documents regeneration of 120 model masks and live Docker re-observation of all 23 FastAPI cases.

## Recompute all saved results

Use Python 3.12 or later from the repository root:

```text
python verify_all.py --output verification-run
```

This command verifies all 70 published SHA-256 digests and reproduces from raw records the archived controlled and FastAPI pilots, the paired 0.5B/7B FastAPI and TodoApp summaries, the four-part support partitions, and the 32 result rows for eight label policies, two models, and two requirement variants.

To replay only the original v1.0.0 archives (`verify_paper_results.py`, `replication-controlled-pilot.zip`, and `replication-restestbench-pilot.zip`):

```text
python verify_paper_results.py score
```

## Live HTTP demonstration

With Python 3.12+ and Docker Desktop (Linux Engine), run:

```powershell
py -3.14 .\http_demo.py --interactive
```

See [DEMO-HTTP.md](DEMO-HTTP.md) for Swagger inspection, interactive pauses, and image building (`--build-images`).

## Compiling the manuscript

Compile `paper.tex` twice with **XeLaTeX** and the ACM `acmart` class (`xelatex -interaction=nonstopmode -halt-on-error paper.tex` via MiKTeX/TeX Live, or on Overleaf with XeLaTeX selected), keeping `api-rates.pdf` in the root directory and `followup/manuscript-results.tex` in `followup/`. After recompiling `paper.tex`, refresh the `paper.pdf` entry in `SHA256SUMS.txt` so `verify_all.py` matches the new PDF digest.

## Contents and third-party material

`SHA256SUMS.txt` records SHA-256 digests for the published artifacts listed in the manifest. Both primary pilot archives preserve their original v1.0.0 bytes and provenance. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for upstream AGPL-3.0 licensing of RESTestBench excerpts.
