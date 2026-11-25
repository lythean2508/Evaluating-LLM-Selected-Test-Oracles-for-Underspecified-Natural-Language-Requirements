"""Generate and score status-oracle selections on the held-out TodoApp pairs."""

import argparse
from hashlib import sha256
from itertools import product
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'api' / 'restest-extension'))

from design import DESCRIPTIONS, Scenario, rule_agrees
from pilot import SEEDS, VARIANTS, collect, make_prompt, read_json, read_lines, write_rows

METRICS = ('selected', 'supported_available', 'supported_selected', 'unsupported_selected',
           'empty', 'supported_raw', 'supported_removed', 'supported_rules_only',
           'supported_missed_by_both')


def verify_frozen():
    for name, expected in read_json(HERE / 'frozen-rules.json').items():
        actual = sha256((ROOT / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Frozen file has changed: {name}')


def evaluation_inputs():
    data = read_json(HERE / 'heldout-requirements.json')
    menu = tuple(data['status_candidates'])
    dataset = {pair['id']: {variant: pair[variant] for variant in VARIANTS}
               for pair in data['pairs']}
    scenarios = {pair['id']: Scenario(pair['path'], pair['path'], pair['method'], pair['fixture'], menu)
                 for pair in data['pairs']}
    if len(dataset) != len(data['pairs']) or not set(menu) <= DESCRIPTIONS.keys():
        raise ValueError('Invalid held-out requirement IDs or assertion candidates')
    return dataset, scenarios, data['contract']


def score(output, dataset, scenarios, spec):
    gold = read_json(HERE / 'heldout-support.json')
    logs = read_lines(output / 'runs.jsonl')
    runs = {(r['id'], r['variant'], r['seed']): r for r in logs}
    expected = set(product(dataset, VARIANTS, SEEDS))
    if set(runs) != expected or len(logs) != len(expected):
        raise ValueError('Missing, unexpected or duplicate held-out runs')

    rows = []
    for req_id, variant in product(dataset, VARIANTS):
        requirement = dataset[req_id][variant]
        scenario = scenarios[req_id]
        menu = scenario.checks
        supported = set(gold[str(req_id)][variant]['supported'])
        if not supported <= set(menu):
            raise ValueError(f'Held-out gold exceeds the menu for {req_id}/{variant}')
        rules = {check for check in menu if rule_agrees(check, requirement)}

        def add_row(method, selected, seed=None, raw=None):
            rows.append({'id': req_id, 'variant': variant, 'method': method, 'seed': seed,
                         'selected_ids': '|'.join(check for check in menu if check in selected),
                         'selected': len(selected), 'supported_available': len(supported),
                         'supported_selected': len(selected & supported),
                         'unsupported_selected': len(selected - supported), 'empty': int(not selected),
                         'supported_raw': len(raw & supported) if raw is not None else None,
                         'supported_removed': len((raw - selected) & supported) if raw is not None else None,
                         'supported_rules_only': len((rules - raw) & supported) if raw is not None else None,
                         'supported_missed_by_both': len(supported - (raw | rules)) if raw is not None else None})

        add_row('rules', rules)
        prompt = make_prompt(requirement, scenario, spec)
        for seed in SEEDS:
            record = runs[req_id, variant, seed]
            decisions = record['response']['content'].strip().split(',')
            if (len(decisions) != len(menu) or set(decisions) - {'Y', 'N'}
                    or record['settings']['prompt'] != prompt or record['settings']['seed'] != seed):
                raise ValueError(f'Invalid or mismatched held-out completion for {req_id}/{variant}/{seed}')
            selected = [check for check, decision in zip(menu, decisions) if decision == 'Y']
            if selected != record['selected']:
                raise ValueError(f'Saved selection disagrees with raw completion for {req_id}/{variant}/{seed}')
            raw = set(selected)
            add_row('llm', raw, seed)
            add_row('llm+gate', raw & rules, seed, raw)

    write_rows(output / 'comparison.csv', rows)
    summary = []
    for variant, method in product(VARIANTS, ('llm', 'llm+gate', 'rules')):
        group = [r for r in rows if r['variant'] == variant and r['method'] == method]
        totals = {key: sum(r[key] for r in group) if group[0][key] is not None else None
                  for key in METRICS}
        summary.append({'variant': variant, 'method': method, 'suites': len(group), **totals})
    write_rows(output / 'summary.csv', summary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('generate', 'score', 'all'))
    parser.add_argument('--url', default='http://127.0.0.1:18862')
    parser.add_argument('--cache-prompt', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify_frozen()
    dataset, scenarios, spec = evaluation_inputs()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.stage in ('generate', 'all'):
        collect(args.output, args.url, dataset=dataset, scenarios=scenarios, spec=spec,
                cache_prompt=args.cache_prompt)
    if args.stage in ('score', 'all'):
        score(args.output, dataset, scenarios, spec)


if __name__ == '__main__':
    main()
