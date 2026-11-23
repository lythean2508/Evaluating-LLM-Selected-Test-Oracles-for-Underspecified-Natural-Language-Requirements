"""Run the controlled requirement-to-test pilot with a local llama.cpp server."""

import argparse
import csv
import json
import operator
import random
import re
from collections import defaultdict
from itertools import product
from pathlib import Path
from time import perf_counter
from urllib.request import Request, urlopen


HERE = Path(__file__).resolve().parent
DOMAIN = range(11)
PROBES = (0, 3, 4, 5, 6, 7, 10)
LABELS = "ABC"
UNKNOWN = "?"
SEEDS = (11, 23, 47)
VARIANTS = ("exact", "partial")
METHODS = ("direct", "abstain", "abstain+gate", "rules")
RELATIONS = {"at least": operator.ge, "at most": operator.le,
             "above": operator.gt, "below": operator.lt}
GRAMMAR = 'root ::= label ("," label){6}\nlabel ::= [ABC?]'
REQUIREMENTS = json.loads((HERE / "requirements.json").read_text(encoding="utf-8"))


def supported_oracles(requirement):
    """Enumerate interpretations using only the visible controlled-language text."""
    usual = re.fullmatch(
        r"The service returns ([ABC]) when x is (at least|at most|above|below) "
        r"(\d+|an unspecified integer cutoff)\. Otherwise it returns "
        r"([ABC]|a different label, which is unspecified)\.", requirement,
    )
    boundary = re.fullmatch(
        r"The service returns ([ABC]) when x is on the (upper|lower) side of (\d+)\. "
        r"The equality rule is unspecified\. (Below|Above) \3 it returns ([ABC])\.",
        requirement,
    )
    if usual:
        success, relation, cutoff, fallback = usual.groups()
        predicates = [RELATIONS[relation]]
        cutoffs = [int(cutoff)] if cutoff.isdecimal() else DOMAIN
        fallbacks = [fallback] if fallback in LABELS else [v for v in LABELS if v != success]
    elif boundary:
        success, side, cutoff, opposite, fallback = boundary.groups()
        if opposite != {"upper": "Below", "lower": "Above"}[side]:
            return (UNKNOWN,) * len(PROBES)
        cutoffs = [int(cutoff)]
        predicates = [operator.gt, operator.ge] if side == "upper" else [operator.lt, operator.le]
        fallbacks = [fallback]
    else:
        return (UNKNOWN,) * len(PROBES)
    values = []
    for x in PROBES:
        possible = {success if predicate(x, limit) else failure
                    for predicate, limit, failure in product(predicates, cutoffs, fallbacks)}
        values.append(next(iter(possible)) if len(possible) == 1 else UNKNOWN)
    return tuple(values)


def make_prompt(requirement, method):
    instruction = {
        "direct": "Predict one output label A, B, or C for each input. Pick your best guess if information is missing.",
        "abstain": "Use A, B, or C only when that answer follows from the requirement for the given input. Use ? whenever multiple labels are possible. Never guess whether a cutoff includes equality or guess a missing cutoff or label.",
    }[method]
    return (
        "<|im_start|>system\nYou design black-box test cases. Follow the requested output format.<|im_end|>\n"
        "<|im_start|>user\nAn API accepts integer x from 0 through 10 and returns one label: A, B, or C. "
        "Any unspecified integer cutoff is also between 0 and 10, inclusive.\n"
        f"Requirement: {requirement}\nInputs, in this order: {', '.join(map(str, PROBES))}.\n"
        f"{instruction}\nOutput exactly seven comma-separated labels in input order. "
        "Use no spaces and no prose.<|im_end|>\n<|im_start|>assistant\n"
    )


def call_model(base_url, prompt, seed):
    settings = {"prompt": prompt, "n_predict": 24, "grammar": GRAMMAR,
                "seed": seed, "temperature": 0.3, "top_k": 40, "top_p": 0.95,
                "cache_prompt": False, "stream": False}
    request = Request(base_url.rstrip("/") + "/completion",
                      data=json.dumps(settings).encode(),
                      headers={"Content-Type": "application/json"})
    start = perf_counter()
    with urlopen(request, timeout=90) as response:
        result = json.load(response)
    return {"settings": settings, "response": result, "seconds": perf_counter() - start}


def collect(base_url, output):
    tasks = list(product(REQUIREMENTS, VARIANTS, METHODS[:2], SEEDS))
    random.Random(20261115).shuffle(tasks)
    raw = output / "runs.jsonl"
    completed = {run_key(r) for r in read_runs(raw)} if raw.exists() else set()
    with raw.open("a", encoding="utf-8") as stream:
        for requirement, variant, method, seed in tasks:
            key = (requirement["id"], variant, method, seed)
            if key in completed:
                continue
            record = dict(zip(("id", "variant", "method", "seed"), key))
            record.update(call_model(base_url, make_prompt(requirement[variant], method), seed))
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            print("Completed", *key, flush=True)


def run_key(record):
    return tuple(record[key] for key in ("id", "variant", "method", "seed"))


def read_runs(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def make_gold(reference):
    relation, limit, success, fallback, missing = reference
    greater = relation.startswith(">")
    inclusive = relation.endswith("=")

    def expected(x):
        if x == limit:
            return success if inclusive else fallback
        same_side = x > limit if greater else x < limit
        return success if same_side else fallback

    exact = tuple(map(expected, PROBES))
    if missing == "comparator":
        partial = tuple(UNKNOWN if x == limit else expected(x) for x in PROBES)
    elif missing == "cutoff":
        # The full bounded domain allows only one decisive extreme for each comparator.
        decisive = {">=": 10, "<=": 0, ">": 0, "<": 10}[relation]
        partial = tuple(expected(x) if x == decisive else UNKNOWN for x in PROBES)
    else:
        partial = tuple(value if value == success else UNKNOWN for value in exact)
    return exact, partial


def mutants(reference):
    relation, limit, success, fallback, _ = reference
    compare = {">=": operator.ge, "<=": operator.le, ">": operator.gt, "<": operator.lt}
    flip = {">=": ">", "<=": "<", ">": ">=", "<": "<="}[relation]
    third = next(label for label in LABELS if label not in (success, fallback))
    original = compare[relation]
    definitions = {
        "toggle_equality": lambda x: success if compare[flip](x, limit) else fallback,
        "cutoff_minus_one": lambda x: success if original(x, limit - 1) else fallback,
        "cutoff_plus_one": lambda x: success if original(x, limit + 1) else fallback,
        "wrong_success": lambda x: third if original(x, limit) else fallback,
        "wrong_fallback": lambda x: success if original(x, limit) else third,
        "swap_branches": lambda x: fallback if original(x, limit) else success,
    }
    def reference_output(x):
        return success if original(x, limit) else fallback

    return {name: tuple(map(fn, PROBES)) for name, fn in definitions.items()
            if any(fn(x) != reference_output(x) for x in DOMAIN)}


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def score(output):
    references = {row[0]: row[1:] for row in json.loads((HERE / "reference.json").read_text())}
    runs = read_runs(output / "runs.jsonl")
    indexed = {run_key(row): row for row in runs}
    expected_keys = {(req["id"], v, m, s) for req, v, m, s in
                     product(REQUIREMENTS, VARIANTS, METHODS[:2], SEEDS)}
    if len(runs) != len(indexed) or set(indexed) != expected_keys:
        raise ValueError("Raw runs contain missing, duplicate or unexpected combinations.")
    probes = []
    suites = []
    for requirement, variant, seed in product(REQUIREMENTS, VARIANTS, SEEDS):
        req_id = requirement["id"]
        reference = references[req_id]
        gold = make_gold(reference)[VARIANTS.index(variant)]
        rules = supported_oracles(requirement[variant])
        results = {"rules": rules}
        for method in METHODS[:2]:
            content = indexed[req_id, variant, method, seed]["response"]["content"].strip()
            if not re.fullmatch(r"[ABC?](,[ABC?]){6}", content):
                raise ValueError(f"Unexpected output from constrained decoder: {req_id}, {variant}, {method}, {seed}: {content!r}")
            results[method] = tuple(content.split(","))
        results["abstain+gate"] = tuple(label if label == support else UNKNOWN
                                        for label, support in zip(results["abstain"], rules))
        for method in METHODS:
            # The deterministic baseline contributes one observation per requirement variant.
            if method == "rules" and seed != SEEDS[0]:
                continue
            common = {"id": req_id, "variant": variant, "missing_component": reference[-1],
                      "method": method, "seed": "" if method == "rules" else seed}
            predicted = results[method]
            for x, label, correct in zip(PROBES, predicted, gold):
                probes.append({**common, "x": x, "oracle": label, "gold": correct})
            if variant == "exact":
                pool = mutants(reference)
                mistaken = any(p != UNKNOWN and p != g for p, g in zip(predicted, gold))
                killed = [name for name, values in pool.items() if not mistaken and
                          any(p != UNKNOWN and p != v for p, v in zip(predicted, values))]
                suites.append({**common, "false_alarm": int(mistaken),
                               "eligible_mutants": len(pool), "killed_mutants": len(killed),
                               "killed_mutant_ids": "|".join(killed)})
    write_csv(output / "oracles.csv", probes)
    write_csv(output / "mutation.csv", suites)
    grouped = defaultdict(list)
    for row in probes:
        grouped[row["method"], row["variant"]].append(row)
        if row["variant"] == "partial":
            grouped[row["method"], row["missing_component"]].append(row)
    summary = []
    for (method, variant), rows in grouped.items():
        known = [r for r in rows if r["gold"] != UNKNOWN]
        unknown = [r for r in rows if r["gold"] == UNKNOWN]
        related = [s for s in suites if s["method"] == method] if variant == "exact" else []
        summary.append({"method": method, "variant": variant, "probes": len(rows),
                        "decidable": len(known), "ambiguous": len(unknown),
                        "correct_on_decidable": sum(r["gold"] == r["oracle"] for r in known),
                        "wrong_on_decidable": sum(r["oracle"] not in (r["gold"], UNKNOWN) for r in known),
                        "asserted_on_ambiguous": sum(r["oracle"] != UNKNOWN for r in unknown),
                        "assertions": sum(r["oracle"] != UNKNOWN for r in rows),
                        "suites": len(related), "false_alarm_suites": sum(s["false_alarm"] for s in related),
                        "eligible_mutants": sum(s["eligible_mutants"] for s in related),
                        "killed_mutants": sum(s["killed_mutants"] for s in related)})
    write_csv(output / "summary.csv", summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("generate", "score", "all"))
    parser.add_argument("--url", default="http://127.0.0.1:18786")
    parser.add_argument("--output", type=Path, default=HERE / "results")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.phase in ("generate", "all"):
        collect(args.url, args.output)
    if args.phase in ("score", "all"):
        score(args.output)


if __name__ == "__main__":
    main()
