# Third-party notices

The API pilot uses requirement extracts, associated mutants, and observations from [RESTestBench](https://github.com/casablancahotelsoftware/RESTestBench), frozen at commit `4decc1e36ea3dd41b64ce3e3ac6a85bc72df36ae`. The upstream license text is preserved at `RESTestBench/LICENSE` inside `replication-restestbench-pilot.zip` (GNU Affero General Public License, version 3). Consult the original archive records for provenance and dependencies.

The manuscript uses the ACM `acmart` LaTeX class, which is an external build dependency and is not bundled here. Model weights, inference runtimes, full service images, and the full benchmark checkout are not included. Their upstream terms apply separately.

This notice does not relicense third-party works or grant an additional license to the authors' original manuscript and code.

The HTTP source archive includes the frozen RESTestBench excerpt and FastAPI template source with their preserved licenses. Shell files use LF line endings for Linux containers. It contains an `.env.example` template; local keys are generated at runtime. Local `.env`, virtual environments, database volumes and Docker images are excluded. The expanded `api/RESTestBench/LICENSE` also preserves the upstream AGPL-3.0 license.
