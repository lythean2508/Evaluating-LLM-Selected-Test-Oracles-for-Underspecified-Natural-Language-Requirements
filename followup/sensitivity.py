"""Evaluate explicit alternative label policies against the frozen FastAPI suites."""

import argparse
from itertools import product
from pathlib import Path

from replay import MODELS, read_rows, replay, write_summary
from design import SCENARIOS
from pilot import HERE as PILOT, read_json

HERE = Path(__file__).resolve().parent
VARIANTS = ('precise', 'vague')
METRICS = ('supported_selected', 'supported_available', 'unsupported_selected',
           'selected', 'qualified', 'killed_if_qualified', 'mutants')


def calculate(replayed):
    original = read_json(PILOT / 'semantic_gold.json')
    baseline_labels = {(req_id, variant): set(original[str(req_id)][variant])
                       for req_id in SCENARIOS for variant in VARIANTS}
    policies = read_json(HERE / 'label-policies.json')
    rows = {model: read_rows(replayed / model / 'api/comparison.csv') for model in MODELS}
    diagnostics = partition(rows, baseline_labels)
    results = []
    for switches in product((False, True), repeat=len(policies)):
        labels = {key: set(values) for key, values in baseline_labels.items()}
        for enabled, policy in zip(switches, policies):
            if enabled:
                for item in policy['exclude']:
                    support = labels[item['id'], item['variant']]
                    if not set(item['checks']) <= support:
                        raise ValueError(f"Policy must remove an existing supported check: {item}")
                    support.difference_update(item['checks'])
        for model, variant in product(MODELS, VARIANTS):
            suite_rows = [r for r in rows[model] if r['method'] == 'llm+gate' and r['variant'] == variant]
            totals = dict.fromkeys(METRICS, 0)
            for row in suite_rows:
                candidate_ids = {key for key in row['selected_ids'].split('|') if key}
                supported = labels[int(row['id']), variant]
                unsupported = candidate_ids - supported
                qualified = bool(int(row['passes_original'])) and not unsupported
                totals['supported_selected'] += len(candidate_ids & supported)
                totals['supported_available'] += len(supported)
                totals['unsupported_selected'] += len(unsupported)
                totals['selected'] += len(candidate_ids)
                totals['qualified'] += int(qualified)
                totals['killed_if_qualified'] += int(row['killed_if_passes_original']) if qualified else 0
                totals['mutants'] += int(row['mutants'])
            if not any(switches):
                summary = read_rows(replayed / model / 'api/summary.csv')
                expected = next(r for r in summary if r['variant'] == variant and r['method'] == 'llm+gate')
                if any(value != int(expected[name]) for name, value in totals.items()):
                    raise ValueError(f'Original-policy score failed reconciliation for {model}/{variant}')
            results.append({'policy': ''.join(str(int(b)) for b in switches),
                            **{p['name']: int(on) for p, on in zip(policies, switches)},
                            'model': model, 'variant': variant, **totals})
    return results, diagnostics


def partition(rows_by_model, labels):
    output = []
    for model, rows in rows_by_model.items():
        rules = {(int(r['id']), r['variant']): set(r['selected_ids'].split('|'))
                 for r in rows if r['method'] == 'rules'}
        for variant in VARIANTS:
            counts = dict.fromkeys(('both', 'model_only', 'rules_only', 'neither'), 0)
            for r in rows:
                if r['method'] != 'llm' or r['variant'] != variant:
                    continue
                key = int(r['id']), variant
                g = labels[key]
                m = g.intersection(r['selected_ids'].split('|'))
                s = g & rules[key]
                counts['both'] += len(m & s)
                counts['model_only'] += len(m - s)
                counts['rules_only'] += len(s - m)
                counts['neither'] += len(g - (m | s))
            output.append({'model': model, 'variant': variant, **counts,
                           'rule_ceiling': counts['both'] + counts['rules_only'],
                           'supported_available': sum(counts.values())})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    directory = args.output.resolve()
    published = (HERE / 'results').resolve()
    if directory == published or published in directory.parents:
        parser.error('--output must be outside the published results directory')
    replay(published, directory / 'replayed')
    results, diagnostics = calculate(directory / 'replayed')
    write_summary(directory / 'label-sensitivity.csv', results)
    write_summary(directory / 'support-partition.csv', diagnostics)
    print(f'Wrote {len(results)} label-policy rows and {len(diagnostics)} support-partition rows.')


if __name__ == '__main__':
    main()
