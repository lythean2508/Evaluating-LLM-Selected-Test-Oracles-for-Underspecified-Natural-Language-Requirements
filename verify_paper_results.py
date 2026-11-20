"""Recompute the paper's figures or reproduce one RESTestBench mutant locally."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from tempfile import mkdtemp
from uuid import uuid4
from zipfile import ZipFile


OUTPUT = Path(__file__).resolve().parent


def live_workspace():
    candidates = (OUTPUT / 'work', OUTPUT.parent / 'work', Path(sys.prefix).resolve().parent)
    for folder in candidates:
        if ((folder / 'restest-extension' / 'observe.py').is_file()
                and (folder / 'RESTestBench' / 'services' / 'fastapi' / 'working'
                     / 'docker-compose.codex.yml').is_file()):
            return folder
    raise RuntimeError('FastAPI demo files were not found. Run with the Python executable in '
                       'the existing work/restest-venv environment, or keep the original work folder '
                       'beside this script or its parent directory.')


def recompute(archive_name, script, summary, destination):
    with ZipFile(OUTPUT / archive_name) as archive:
        saved = archive.read(summary)
        for entry in archive.infolist():
            if not (destination / entry.filename).resolve().is_relative_to(destination):
                raise ValueError(f'Invalid archive member: {entry.filename}')
        archive.extractall(destination)
    subprocess.run([sys.executable, str(destination / script), 'score'], cwd=destination, check=True)
    with (destination / summary).open(encoding='utf-8-sig', newline='') as source:
        rows = list(csv.DictReader(source))
    if (destination / summary).read_bytes() != saved:
        raise ValueError(f'Recomputed summary differs from the saved archive: {archive_name}')
    return {(row['variant'], row['method']): row for row in rows}


def fraction(row, numerator, denominator):
    return f'{row[numerator]}/{row[denominator]}'


def score():
    root = Path(mkdtemp(prefix='defense-score-'))
    synthetic = root / 'controlled'
    api = root / 'fastapi'
    threshold = recompute('replication-controlled-pilot.zip', 'study.py',
                          'results/summary.csv', synthetic)
    results = recompute('replication-restestbench-pilot.zip', 'restest-extension/pilot.py',
                        'restest-extension/results/summary.csv', api)
    before = threshold['partial', 'abstain']
    after = threshold['partial', 'abstain+gate']
    rules = threshold['partial', 'rules']
    numeric = (fraction(before, 'asserted_on_ambiguous', 'ambiguous'),
               fraction(after, 'asserted_on_ambiguous', 'ambiguous'),
               fraction(after, 'correct_on_decidable', 'decidable'),
               fraction(rules, 'correct_on_decidable', 'decidable'))
    if numeric != ('58/126', '0/126', '29/126', '42/42'):
        raise ValueError('Controlled results differ from the figures in the paper')
    print('CONTROLLED PILOT (12 paired requirements)')
    print(f'Unsupported guesses: {numeric[0]} -> {numeric[1]} with filtering')
    print(f'Supported probes retained: {numeric[2]} filtered, {numeric[3]} rules')
    print('\nFASTAPI SUMMARY (6 paired requirements, 17 mutants)')
    print(f'{"Input":<9} {"Method":<10} {"Grounded":>9} {"Unsupported":>12} {"Kills":>8}')
    expected = {
        'precise': (('47/81', '26/73', '2/51'), ('47/81', '0/47', '32/51'), ('27/27', '0/27', '17/17')),
        'vague': (('28/48', '56/84', '0/51'), ('17/48', '0/17', '19/51'), ('9/16', '0/9', '10/17')),
    }
    for variant, entries in expected.items():
        for method, target in zip(('llm', 'llm+gate', 'rules'), entries):
            row = results[variant, method]
            metrics = (fraction(row, 'supported_selected', 'supported_available'),
                       fraction(row, 'unsupported_selected', 'selected'),
                       fraction(row, 'killed_if_qualified', 'mutants'))
            if metrics != target:
                raise ValueError(f'Table 1 mismatch for {variant}/{method}')
            print(f'{variant:<9} {method:<10} {metrics[0]:>9} {metrics[1]:>12} {metrics[2]:>8}')
    print('\nPASS: Both summaries were recomputed and match the paper.')
    print(f'Replayed files: {root}')


def live():
    work = live_workspace()
    repo = work / 'RESTestBench'
    docker = shutil.which('docker')
    if not docker:
        raise RuntimeError('Docker command not found. Open Docker Desktop and a new PowerShell window.')
    sys.path.insert(0, str(work / 'restest-extension'))
    from observe import API, PASSWORD, body, wait_ready
    from src.mutator import Mutant, Mutator

    def docker_call(args, *, cwd=None, env=None, capture=False):
        return subprocess.run([docker, *args], cwd=cwd, env=env, check=True, text=True,
                              capture_output=capture, timeout=160)

    docker_call(['version', '--format', '{{.Server.Version}}'], capture=True)
    docker_call(['image', 'inspect', 'restestbench-codex-fastapi-backend:4decc1e',
                 'postgres:17'], capture=True)
    with socket.socket() as connection:
        connection.settimeout(0.5)
        if connection.connect_ex(('127.0.0.1', 8000)) == 0:
            raise RuntimeError('Port 8000 is already occupied. Stop the existing local service first.')

    source = repo / 'services' / 'fastapi'
    root = Path(mkdtemp(prefix='defense-live-', dir=work))
    checkout = root / 'fastapi'
    shutil.copytree(source / 'original', checkout)
    shutil.copy2(source / 'working' / 'docker-compose.codex.yml', checkout)
    env = {
        **os.environ,
        'COMPOSE_PROJECT_NAME': 'restestbench-defense-' + uuid4().hex[:8],
        'COMPOSE_PATH_SEPARATOR': '|',
        'COMPOSE_FILE': 'docker-compose.yml|docker-compose.override.yml|docker-compose.codex.yml',
        'DOCKER_IMAGE_BACKEND': 'restestbench-codex-fastapi-backend',
        'DOCKER_IMAGE_FRONTEND': 'restestbench-codex-fastapi-frontend',
        'TAG': '4decc1e',
        'CI': 'false',
    }

    def compose(*args, capture=False):
        return docker_call(['compose', *args], cwd=checkout, env=env, capture=capture)

    def request(api):
        owner = api.token(api.account(), PASSWORD)
        reader = api.token(api.account(), PASSWORD)
        item = api.item(owner)
        response = api.send('GET', '/api/v1/items/' + item['id'], reader)
        return response.status_code, body(response).get('detail')

    definition_path = repo / 'data' / 'requirements' / 'fastapi' / 'requirement_4.json'
    definition = json.loads(definition_path.read_text(encoding='utf-8'))
    mutant = Mutant.from_dict(definition['mutants'][2])
    file = (checkout / mutant.file).resolve()
    if not file.is_relative_to(checkout / 'backend' / 'app'):
        raise ValueError('Invalid mutant file')
    original = file.read_bytes()
    api = API()

    print('Starting the isolated FastAPI example for requirement 4...', flush=True)
    try:
        compose('up', '-d', '--no-build', '--pull', 'never', 'db', 'prestart', 'backend')
        wait_ready(api)
        before = request(api)
        if not Mutator(checkout).apply_mutation(mutant):
            raise RuntimeError('RESTestBench mutant could not be applied')
        compose('restart', '--timeout', '2', 'backend')
        wait_ready(api)
        mounted = '/app/' + file.relative_to(checkout / 'backend').as_posix()
        digest = compose('exec', '-T', 'backend', 'python', '-c',
                         'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())',
                         mounted, capture=True).stdout.strip()
        if digest != hashlib.sha256(file.read_bytes()).hexdigest() or file.read_bytes() == original:
            raise RuntimeError('Modified code was not verified in the running container')
        after = request(api)
        checks = {
            'Vague | HTTP is 4xx': lambda value: 400 <= value[0] < 500,
            'Precise | HTTP 400 and expected detail': lambda value: value == (400, 'Not enough permissions'),
        }
        print(f'\nOriginal response: HTTP {before[0]}, detail={before[1]!r}')
        print(f'Mutant response:   HTTP {after[0]}, detail={after[1]!r}\n')
        print(f'{"Oracle":<41} {"Original":>9} {"Mutant":>9}')
        for name, check in checks.items():
            print(f'{name:<41} {"PASS" if check(before) else "FAIL":>9} {"PASS" if check(after) else "FAIL":>9}')
        if (before, after) != ((400, 'Not enough permissions'), (400, 'Item not found')):
            raise RuntimeError('Observed API responses differ from the expected demonstration')
        print('\nPASS: Both real HTTP responses reproduced. The precise check detected the mutant.')
    finally:
        file.write_bytes(original)
        compose('down', '--volumes', '--timeout', '2')


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('mode', choices=('score', 'live'))
    mode = cli.parse_args().mode
    try:
        {'score': score, 'live': live}[mode]()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.strip(), file=sys.stderr)
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(1)
