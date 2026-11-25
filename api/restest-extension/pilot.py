"""Generate assertion suites and score the frozen six-pair RESTestBench pilot."""

import argparse
import csv
import json
from itertools import product
from pathlib import Path
from time import perf_counter
from urllib.request import Request, ProxyHandler, build_opener

from design import DESCRIPTIONS, SCENARIOS, rule_agrees


HERE = Path(__file__).resolve().parent
REPO = HERE.parent / 'RESTestBench'
VARIANTS = ('precise', 'vague')
METHODS = ('llm', 'llm+gate', 'rules')
SEEDS = (11, 23, 47)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def texts():
    return {req_id: {v: row[f'requirement_{v}'] for v in VARIANTS}
            for req_id in SCENARIOS
            for row in [read_json(REPO / f'data/requirements/fastapi/requirement_{req_id}.json')]}


def make_prompt(requirement, scenario, spec):
    route = spec['paths'][scenario.path][scenario.method]
    context = {'method': scenario.method.upper(), 'path': scenario.path,
               'operation': route['operationId'],
               'response_schema': {code: fields.get('content', {})
                                   for code, fields in route['responses'].items()}}
    candidates = '\n'.join(f'{index}. {DESCRIPTIONS[check]}'
                           for index, check in enumerate(scenario.checks, 1))
    return (
        '<|im_start|>system\nYou select assertions for a black-box test. '
        'Use Y for a justified assertion and N to leave it out. Output only comma-separated letters. '
        'An exact status or error message needs support in the requirement. A general success or rejection '
        'may justify checking the status class. The API schema describes the interface. '
        'Do not infer an exact error for a specific scenario from a default response in the schema. '
        'Example: when the requirement says "Reject an order with no items", reject with 4xx is Y, '
        'HTTP 401 is N, and detail equals "Empty order" is N.<|im_end|>\n'
        '<|im_start|>user\n'
        f'API contract: {json.dumps(context, separators=(",", ":"))}\n'
        f'Fixed scenario: {scenario.fixture}\n'
        f'Visible requirement: {requirement}\n'
        f'Test assertions to consider:\n{candidates}\n'
        f'Output exactly {len(scenario.checks)} Y or N decisions in this order, separated by commas.'
        '<|im_end|>\n<|im_start|>assistant\n'
    )


def collect(output, url, *, dataset=None, scenarios=SCENARIOS, spec=None, cache_prompt=False):
    if dataset is None:
        dataset = texts()
    if spec is None:
        spec = read_json(REPO / 'services/fastapi/spec.json')
    path = output / 'runs.jsonl'
    previous = read_lines(path) if path.exists() else []
    completed = {(r['id'], r['variant'], r['seed']): r for r in previous}
    if len(completed) != len(previous):
        raise ValueError('Duplicate model runs')
    opener = build_opener(ProxyHandler({}))
    with path.open('a', encoding='utf-8') as sink:
        for req_id, variant, seed in product(scenarios, VARIANTS, SEEDS):
            scenario = scenarios[req_id]
            settings = {
                'prompt': make_prompt(dataset[req_id][variant], scenario, spec),
                'n_predict': 32, 'seed': seed, 'temperature': 0.3, 'top_k': 40,
                'top_p': 0.95, 'cache_prompt': cache_prompt,
                'grammar': 'root ::= label ("," label){' + str(len(scenario.checks) - 1) + '}\nlabel ::= [YN]',
            }
            existing = completed.get((req_id, variant, seed))
            if existing is not None:
                if existing['settings'] != settings:
                    raise ValueError(f'Saved settings differ for R{req_id}/{variant}/{seed}')
                continue
            start = perf_counter()
            request = Request(url.rstrip('/') + '/completion', json.dumps(settings).encode(),
                              {'Content-Type': 'application/json'})
            with opener.open(request, timeout=100) as response:
                result = json.load(response)
            decisions = result['content'].strip().split(',')
            if len(decisions) != len(scenario.checks) or set(decisions) - {'Y', 'N'}:
                raise ValueError(f'Invalid model response for {req_id}, {variant}, {seed}: {decisions!r}')
            record = {'id': req_id, 'variant': variant, 'seed': seed, 'settings': settings,
                      'response': result, 'selected': [check for check, decision in
                                                       zip(scenario.checks, decisions) if decision == 'Y'],
                      'seconds': perf_counter() - start}
            sink.write(json.dumps(record, ensure_ascii=False) + '\n')
            sink.flush()
            print(f'Generated R{req_id}/{variant}/{seed}: {len(record["selected"])} assertions', flush=True)


def read_lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def write_rows(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as sink:
        writer = csv.DictWriter(sink, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def score(output):
    dataset = texts()
    gold = read_json(HERE / 'semantic_gold.json')
    runs = read_lines(output / 'runs.jsonl')
    plans = {(r['id'], r['variant'], r['seed']): set(r['selected']) for r in runs}
    expected = set(product(SCENARIOS, VARIANTS, SEEDS))
    if len(runs) != len(plans) or set(plans) != expected:
        raise ValueError('Incomplete or duplicate model runs')
    observations = read_lines(output / 'observations.jsonl')
    indexed = {(r['id'], r['mutant']): r for r in observations}
    keys = set()
    for req_id in SCENARIOS:
        req = read_json(REPO / f'data/requirements/fastapi/requirement_{req_id}.json')
        keys.add((req_id, None))
        keys.update((req_id, index) for index in range(len(req['mutants'])))
    if len(observations) != len(indexed) or set(indexed) != keys:
        raise ValueError('Incomplete or duplicate API observations')

    rows = []
    for req_id, variant, method in product(SCENARIOS, VARIANTS, METHODS):
        scenario = SCENARIOS[req_id]
        supported = set(gold[str(req_id)][variant])
        checks = set(scenario.checks)
        if not supported <= checks:
            raise ValueError('Semantic gold does not match available assertion menu')
        rules = {check for check in checks if rule_agrees(check, dataset[req_id][variant])}
        original = indexed[req_id, None]['checks']
        if not all(original[check] for check in supported):
            raise ValueError(f'Semantic gold and original behavior disagree for R{req_id}/{variant}')
        mutants = {idx: row['checks'] for (r, idx), row in indexed.items() if r == req_id and idx is not None}
        observable_mutants = sum(any(not values[check] for check in supported) for values in mutants.values())
        for seed in (None,) if method == 'rules' else SEEDS:
            if method == 'rules':
                selected = rules
            else:
                selected = plans[req_id, variant, seed]
                if method == 'llm+gate':
                    selected = selected & rules
            if not selected <= checks:
                raise ValueError('Unknown selected assertion')
            canonical = bool(selected) and all(original[check] for check in selected)
            qualified = canonical and selected <= supported
            killed = sorted(idx for idx, values in mutants.items()
                            if canonical and any(not values[check] for check in selected))
            rows.append({'id': req_id, 'variant': variant, 'method': method,
                         'seed': seed, 'selected': len(selected), 'selected_ids': '|'.join(sorted(selected)),
                         'supported_available': len(supported), 'supported_selected': len(selected & supported),
                         'unsupported_available': len(checks - supported),
                         'unsupported_selected': len(selected - supported),
                         'unsupported_ids': '|'.join(sorted(selected - supported)),
                         'empty': int(not selected), 'passes_original': int(canonical),
                         'qualified': int(qualified), 'mutants': len(mutants),
                         'observable_mutants': observable_mutants,
                         'killed_if_passes_original': len(killed),
                         'killed_if_qualified': len(killed) if qualified else 0,
                         'killed_ids': '|'.join(map(str, killed))})
    write_rows(output / 'comparison.csv', rows)
    summary = []
    counts = ('selected', 'supported_available', 'supported_selected', 'unsupported_available',
              'unsupported_selected', 'empty', 'passes_original', 'qualified', 'mutants', 'observable_mutants',
              'killed_if_passes_original', 'killed_if_qualified')
    for variant, method in product((*VARIANTS, 'all'), METHODS):
        subset = [r for r in rows if r['method'] == method and variant in (r['variant'], 'all')]
        summary.append({'variant': variant, 'method': method, 'suites': len(subset),
                        **{count: sum(row[count] for row in subset) for count in counts}})
    write_rows(output / 'summary.csv', summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('generate', 'score'))
    parser.add_argument('--output', type=Path, default=HERE / 'results')
    parser.add_argument('--url', default='http://127.0.0.1:18786')
    parser.add_argument('--cache-prompt', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.stage == 'generate':
        collect(args.output, args.url, cache_prompt=args.cache_prompt)
    else:
        score(args.output)


if __name__ == '__main__':
    main()
