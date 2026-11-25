"""Replay the Qwen model-size comparison and held-out transfer from saved runs."""

import argparse
from collections import defaultdict
import csv
from pathlib import Path
import shutil

from heldout import ROOT, evaluation_inputs, score as score_heldout, verify_frozen
from design import SCENARIOS
from pilot import read_lines, score as score_api

DATASETS = {
    'api': ('id', 'variant', 'seed'),
    'heldout': ('id', 'variant', 'seed'),
}
MODELS = ('qwen-0.5b', 'qwen-7b')


def matched_runs(directory, keys):
    logs = read_lines(directory / 'runs.jsonl')
    rows = {tuple(row[key] for key in keys): row for row in logs}
    if len(rows) != len(logs) or any(row['response'].get('truncated') for row in logs):
        raise ValueError(f'Duplicate or truncated completion in {directory}')
    return rows


def verify_api_masks(records):
    for (req_id, variant, seed), record in records.items():
        decisions = record['response']['content'].strip().split(',')
        menu = SCENARIOS[req_id].checks
        if len(decisions) != len(menu) or set(decisions) - {'Y', 'N'}:
            raise ValueError(f'Invalid FastAPI completion for R{req_id}/{variant}/{seed}')
        selected = [check for check, decision in zip(menu, decisions) if decision == 'Y']
        if selected != record['selected']:
            raise ValueError(f'FastAPI selections disagree with raw completion for R{req_id}/{variant}/{seed}')


def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def write_summary(path, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def vague_filtered_rows(output):
    metrics = ('supported_selected', 'supported_available', 'killed_if_qualified', 'mutants')
    for model in MODELS:
        grouped = defaultdict(list)
        for row in read_rows(output / model / 'api/comparison.csv'):
            if row['variant'] == 'vague' and row['method'] == 'llm+gate':
                grouped[int(row['id'])].append(row)
        for req_id, rows in sorted(grouped.items()):
            yield {'model': model, 'id': req_id, 'seed_evaluations': len(rows),
                   **{name: sum(int(row[name]) for row in rows) for name in metrics}}


def replay(results, output):
    verify_frozen()
    dataset, scenarios, spec = evaluation_inputs()
    baseline = ROOT / 'api/restest-extension/results'
    for dataset_name, keys in DATASETS.items():
        runs = [matched_runs(results / model / dataset_name, keys) for model in MODELS]
        for model, records in zip(MODELS, runs):
            if any(row['response'].get('model') != model for row in records.values()):
                raise ValueError(f'Model alias does not match output directory for {model}/{dataset_name}')
        if runs[0].keys() != runs[1].keys():
            raise ValueError(f'Models cover different tasks in {dataset_name}')
        if any(runs[0][key]['settings'] != runs[1][key]['settings'] for key in runs[0]):
            raise ValueError(f'Models use different settings in {dataset_name}')
        if dataset_name != 'api':
            continue
        for records in runs:
            verify_api_masks(records)
        archived = matched_runs(baseline, keys)
        if archived.keys() != runs[0].keys():
            raise ValueError(f'Original pilot coverage changed in {dataset_name}')
        if any({**archived[key]['settings'], 'cache_prompt': True} != runs[0][key]['settings']
               for key in archived):
            raise ValueError(f'Original pilot settings changed in {dataset_name}')
        agreement = sum(archived[key]['response']['content'].strip() ==
                        runs[0][key]['response']['content'].strip() for key in archived)
        print(f'{dataset_name}: regenerated 0.5B agrees with {agreement}/{len(archived)} archived outputs')

    for model in MODELS:
        for dataset_name in DATASETS:
            directory = output / model / dataset_name
            directory.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(results / model / dataset_name / 'runs.jsonl', directory / 'runs.jsonl')
        directory = output / model
        shutil.copyfile(baseline / 'observations.jsonl', directory / 'api/observations.jsonl')
        score_api(directory / 'api')
        score_heldout(directory / 'heldout', dataset, scenarios, spec)

    for dataset_name in DATASETS:
        combined = [{'model': model, **row} for model in MODELS
                    for row in read_rows(output / model / dataset_name / 'summary.csv')]
        write_summary(output / f'{dataset_name}-summary.csv', combined)
    write_summary(output / 'api-vague-filtered-by-requirement.csv', list(vague_filtered_rows(output)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=Path(__file__).resolve().parent / 'results')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.results.resolve() == args.output.resolve():
        parser.error('--output must differ from --results')
    replay(args.results, args.output)


if __name__ == '__main__':
    main()
