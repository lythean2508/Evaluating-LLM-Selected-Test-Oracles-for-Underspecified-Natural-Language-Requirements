# Model size and frozen rules results

This follow-up runs Qwen2.5-0.5B-Instruct and Qwen2.5-7B-Instruct on paired API tasks. Each model has 36 completions on the six original FastAPI pairs and 24 on four held-out TodoApp pairs. FastAPI scoring reuses the original service and mutant observations. TodoApp scoring evaluates whether a selected status assertion follows from the visible requirement and its fixed scenario.

## Scope and evidence

- [Protocol freeze](https://github.com/lythean2508/Evaluating-LLM-Selected-Test-Oracles-for-Underspecified-Natural-Language-Requirements/commit/54e9872988ad72da2082a1e876759c48decfb5b0) records the unchanged rule files and the selection criteria before the TodoApp text was screened.
- [Held-out sample and label freeze](https://github.com/lythean2508/Evaluating-LLM-Selected-Test-Oracles-for-Underspecified-Natural-Language-Requirements/commit/e1b68ea26fe7b2c71eb56fac7f21096e577a19b9) records the text, fixed fixture, and one set of support labels before TodoApp inference. Screening all 14 requirements produced four eligible distinct method–route pairs under the six-pair cap. The files record the ten exclusions and the rationale for each support label.
- The paired size comparison covers both API cohorts. The archived controlled-language pilot remains a separate 0.5B experiment. A CPU-only 7B trial exceeded the existing request timeout, so both models in the paired API comparison use Vulkan on the same machine. The API collectors reuse prompt prefixes to reduce execution time. The original prompt text, seed schedule, sampling parameters, output grammar, and assertion order remain in use on FastAPI. The runner and replay verifier record the additional settings and check matching configurations.
- The held-out status task uses one annotation set and excludes requirements for which the outcome of the measured operation is an authentication, authorization, or security property. Field values and persistence are outside its status-only assertion menu. The rule freeze controls tuning on the new texts. Upstream exposure in model training and label disagreement remain unmeasured.

## Recompute the results

Run from the repository root with Python 3.11 or later. The replay reads the saved model completions, checks the frozen rules and paired parameters, and writes the four per-cohort and per-model result sets plus the two combined summaries. It uses the archived FastAPI responses.

```text
python followup/replay.py --output followup-replay
```

[FastAPI summaries](results/api-summary.csv) · [TodoApp summaries](results/heldout-summary.csv) · [Execution provenance](environment.json)

## Regenerate model completions

Use [llama.cpp b5046](https://github.com/ggml-org/llama.cpp/releases/tag/b5046) and the GGUF revisions and checksums recorded in [environment.json](environment.json). Use the first 7B shard as the model argument and keep the second shard beside it. The original run used the Windows Vulkan build and the following commands. Replace the executable and weight paths with yours. The `--gpu-layers` default of `0` also supports a local CPU run on suitable hardware.

```powershell
python followup/run_api.py --server C:\llama\llama-server.exe --model C:\models\qwen2.5-0.5b-instruct-q4_k_m.gguf --alias qwen-0.5b --output new-runs/qwen-0.5b --gpu-layers 99
python followup/run_api.py --server C:\llama\llama-server.exe --model C:\models\qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf --alias qwen-7b --output new-runs/qwen-7b --gpu-layers 99
python followup/replay.py --results new-runs --output new-scores
```

The [held-out requirements](heldout-requirements.json) include excerpts and a minimal response contract from [RESTestBench](https://github.com/casablancahotelsoftware/RESTestBench) at its pinned revision. The upstream material is available under [the preserved AGPL-3.0 license](../api/RESTestBench/LICENSE).

## Findings

| Cohort and requirement variant | Filtered supported coverage at 0.5B → 7B | Qualified detections at 0.5B → 7B |
| --- | --- | --- |
| FastAPI precise | 50/81 → 47/81 | 36/51 → 37/51 |
| FastAPI vague | 18/48 → 20/48 | 22/51 → 21/51 |
| TodoApp precise | 7/24 → 10/24 | Outside the TodoApp outcome set |
| TodoApp vague | 0/12 → 0/12 | Outside the TodoApp outcome set |

On vague FastAPI, 7B selects 36/48 supported opportunities before filtering and preserves 20 of those 36. The 0.5B model selects 31/48 and preserves 18 of those 31. The fraction of raw supported choices retained therefore moves from 58.1% to 55.6%, despite the larger absolute count. On vague TodoApp, the frozen rules contribute no candidates, so each model produces 12 empty filtered suites. On precise TodoApp, the rules cover 7/8 supported status candidates and also choose one unsupported check for the deletion scenario. A status mentioned for a follow-up GET is picked as an assertion about DELETE. The unsupported assertion survives the intersection in 2 out of 9 selected checks at 0.5B and 3 out of 13 at 7B.

The matched Vulkan 0.5B FastAPI run agrees with 16/36 archived CPU masks. A separate 0.5B CPU rerun with the original configurations reproduced all 36 FastAPI and all 144 controlled completions. The results above use the matched Vulkan pair for model comparisons.
