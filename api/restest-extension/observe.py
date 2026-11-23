"""Run each frozen API scenario on the original and its RESTestBench mutants."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4

import requests

from design import SCENARIOS
from pilot import HERE, REPO, read_json, read_lines


sys.path.insert(0, str(REPO))
from src.mutator import Mutant, Mutator


BASE = 'http://127.0.0.1:8000'
SERVICE = REPO / 'services/fastapi'
WORKING = SERVICE / 'working'
ADMIN = ('admin@example.com', 'password123')
PASSWORD = 'Bench-local-1234'


def compose(*args):
    return subprocess.check_output(['docker', 'compose', *args], cwd=WORKING, text=True,
                                   timeout=160).strip()


def body(response):
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


class API:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False

    def send(self, method, path, token=None, **kwargs):
        headers = {'Authorization': f'Bearer {token}'} if token else None
        return self.session.request(method, BASE + path, headers=headers, timeout=12, **kwargs)

    def login(self, email, password):
        return self.send('POST', '/api/v1/login/access-token', data={'username': email, 'password': password})

    def token(self, email, password):
        response = self.login(email, password)
        return checked(response, 'access_token', 'login fixture')

    def register(self, email, name):
        return self.send('POST', '/api/v1/users/signup',
                         json={'email': email, 'password': PASSWORD, 'full_name': name})

    def account(self):
        email = email_for_run()
        checked(self.register(email, 'Fixture Account'), 'id', 'signup fixture')
        return email

    def item(self, token):
        response = self.send('POST', '/api/v1/items/', token,
                             json={'title': 'Initial title', 'description': 'Initial description'})
        checked(response, 'id', 'create item fixture')
        return body(response)


def email_for_run():
    return f'pair-{uuid4().hex}@example.com'


def checked(response, field, stage):
    value = body(response).get(field)
    if not response.ok or not value:
        raise RuntimeError(f'Fixture failed in {stage}: HTTP {response.status_code}, missing or invalid {field}')
    return value


def wait_ready(api):
    deadline = monotonic() + 70
    while monotonic() < deadline:
        try:
            if api.send('GET', '/api/v1/utils/health-check/').status_code == 200:
                return
        except requests.RequestException:
            pass
        sleep(0.8)
    raise RuntimeError('FastAPI did not become healthy')


def assert_mounted(path):
    mount = '/app/' + path.relative_to(WORKING / 'backend').as_posix()
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    digest = compose('exec', '-T', 'backend', 'python', '-c',
                     'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())', mount)
    if digest != expected:
        raise RuntimeError('The running container does not see the selected source file')
    return expected


def probe(api, req_id):
    extra = {}
    secondary = None
    if req_id in (2, 3, 6):
        token = api.token(*ADMIN)
        item = api.item(token) if req_id != 3 else {'id': str(uuid4())}
        endpoint = '/api/v1/items/' + item['id']
        if req_id == 6:
            updated = {'title': 'Updated title', 'description': 'Updated description'}
            response = api.send('PUT', endpoint, token, json=updated)
            extra = {f'updated_{key}': body(response).get(key) == value for key, value in updated.items()}
        else:
            response = api.send('GET', endpoint, token)
        if req_id in (2, 6):
            for field, name in (('title', 'same_title'), ('description', 'same_description'),
                                ('id', 'same_id'), ('owner_id', 'same_owner')):
                extra[name] = field in item and field in body(response) and body(response)[field] == item[field]
    elif req_id == 4:
        owner, stranger = (api.token(api.account(), PASSWORD) for _ in range(2))
        item = api.item(owner)
        response = api.send('GET', '/api/v1/items/' + item['id'], stranger)
    elif req_id == 13:
        response = api.login(api.account(), 'Bench-local-incorrect')
    elif req_id == 34:
        email = email_for_run()
        name = 'Expected Full Name'
        response = api.register(email, name)
        login = api.login(email, PASSWORD)
        secondary = login.status_code
        extra = {'same_email': body(response).get('email') == email,
                 'same_name': body(response).get('full_name') == name,
                 'has_user_id': bool(body(response).get('id')),
                 'can_login': login.ok and bool(body(login).get('access_token'))}
    else:
        raise ValueError(f'Unknown fixed scenario: {req_id}')

    status = response.status_code
    detail = body(response).get('detail')
    token = bool(body(response).get('access_token'))
    observed = {
        **{f'http_{code}': status == code for code in (200, 400, 401, 403, 404, 422)},
        'success': 200 <= status < 300, 'denied': 400 <= status < 500,
        'item_not_found': detail == 'Item not found', 'no_permission': detail == 'Not enough permissions',
        'wrong_password': detail == 'Incorrect email or password', 'has_token': token, 'no_token': not token,
        **extra,
    }
    return {'http_status': status, 'followup_status': secondary,
            'checks': {check: observed[check] for check in SCENARIOS[req_id].checks}}


def observe(output):
    output.mkdir(exist_ok=True, parents=True)
    records = output / 'observations.jsonl'
    already = {(r['id'], r['mutant']) for r in read_lines(records)} if records.exists() else set()
    definitions = {rid: read_json(REPO / f'data/requirements/fastapi/requirement_{rid}.json')['mutants']
                   for rid in SCENARIOS}
    originals = {}
    for mutants in definitions.values():
        for mutant in mutants:
            relative = Path(mutant['file'])
            target = (WORKING / relative).resolve()
            if not target.is_relative_to((WORKING / 'backend/app').resolve()):
                raise ValueError(f'Mutant escaped the FastAPI working application: {relative}')
            originals[target] = (SERVICE / 'original' / relative).read_bytes()
            if target.read_bytes() != originals[target]:
                raise RuntimeError(f'Working tree is not pristine: {relative}')

    def record(sink, api, rid, key, sha=None):
        row = {'id': rid, 'mutant': key, 'source_sha256': sha, **probe(api, rid)}
        sink.write(json.dumps(row) + '\n')
        sink.flush()
        print(f'Observed R{rid}/{key if key is not None else "original"}: HTTP {row["http_status"]}', flush=True)

    api = API()
    wait_ready(api)
    for target in originals:
        assert_mounted(target)
    with records.open('a', encoding='utf-8') as sink:
        for rid in SCENARIOS:
            if (rid, None) not in already:
                record(sink, api, rid, None)
        mutator = Mutator(WORKING)
        for rid, mutants in definitions.items():
            for index, data in enumerate(mutants):
                if (rid, index) in already:
                    continue
                target = (WORKING / data['file']).resolve()
                try:
                    if not mutator.apply_mutation(Mutant.from_dict(data)):
                        raise RuntimeError(f'Mutant could not be applied: R{rid}/{index}')
                    if target.read_bytes() == originals[target]:
                        raise RuntimeError(f'Mutant did not change the edited file: R{rid}/{index}')
                    compose('restart', '--timeout', '2', 'backend')
                    wait_ready(api)
                    sha = assert_mounted(target)
                    record(sink, api, rid, index, sha)
                finally:
                    target.write_bytes(originals[target])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE / 'results')
    observe(parser.parse_args().output)
