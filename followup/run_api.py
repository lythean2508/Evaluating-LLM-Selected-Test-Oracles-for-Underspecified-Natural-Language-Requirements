"""Run both API cohorts against one local llama.cpp server."""

import argparse
from contextlib import suppress
import json
from pathlib import Path
import subprocess
from time import monotonic, sleep
from urllib.request import ProxyHandler, build_opener

from heldout import collect, evaluation_inputs, verify_frozen


def wait_for_server(server, url):
    opener = build_opener(ProxyHandler({}))
    deadline = monotonic() + 240
    while monotonic() < deadline and server.poll() is None:
        with suppress(OSError):
            with opener.open(url + '/health', timeout=4) as response:
                if json.load(response).get('status') == 'ok':
                    return
        sleep(1)
    raise RuntimeError('llama.cpp did not become ready. See server.log in the output directory.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--alias', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--port', type=int, default=18862)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--gpu-layers', type=int, default=0)
    args = parser.parse_args()
    verify_frozen()
    dataset, scenarios, spec = evaluation_inputs()
    args.output.mkdir(parents=True, exist_ok=True)
    url = f'http://127.0.0.1:{args.port}'
    executable = args.server.resolve()
    command = [str(executable), '--host', '127.0.0.1', '--port', str(args.port),
               '-t', str(args.threads), '-c', '2048', '-ngl', str(args.gpu_layers), '-np', '1',
               '--alias', args.alias, '-m', str(args.model.resolve())]
    with (args.output / 'server.log').open('ab') as log:
        server = subprocess.Popen(command, cwd=executable.parent, stdout=log, stderr=subprocess.STDOUT,
                                  creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            wait_for_server(server, url)
            heldout = args.output / 'heldout'
            heldout.mkdir(exist_ok=True)
            collect(heldout, url, dataset=dataset, scenarios=scenarios, spec=spec, cache_prompt=True)
            pilot = args.output / 'api'
            pilot.mkdir(exist_ok=True)
            collect(pilot, url, cache_prompt=True)
        finally:
            if server.poll() is None:
                server.terminate()
                server.wait(timeout=15)


if __name__ == '__main__':
    main()
