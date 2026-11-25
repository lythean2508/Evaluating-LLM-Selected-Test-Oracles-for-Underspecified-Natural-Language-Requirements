"""Verify checksums and reproduce the paper's archived numerical tables."""

import argparse
from hashlib import file_digest
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def verify_manifest():
    entries = (ROOT / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines()
    for row in entries:
        expected, relative = row.split('  ', 1)
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError(f'Manifest path escapes the repository: {relative}')
        with path.open('rb') as source:
            actual = file_digest(source, 'sha256').hexdigest()
        if actual != expected:
            raise ValueError(f'Published checksum differs: {relative}')
    print(f'PASS: {len(entries)} published SHA-256 digests verified.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    verify_manifest()
    subprocess.run([sys.executable, str(ROOT / 'verify_paper_results.py'), 'score'], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / 'followup/sensitivity.py'), '--output', str(output)],
                   check=True, cwd=ROOT)
    published = ROOT / 'followup/results'
    for expected in sorted(published.glob('*.csv')):
        folder = output if expected.name in ('label-sensitivity.csv', 'support-partition.csv') else output / 'replayed'
        fresh = folder / expected.name
        if expected.read_bytes() != fresh.read_bytes():
            raise ValueError(f'Replayed CSV differs: {expected.name}')
        print(f'MATCH: {expected.name}')
    print('PASS: archived pilots, paired follow-up, and label-policy sensitivity reproduced.')


if __name__ == '__main__':
    main()
