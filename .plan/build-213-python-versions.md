# Plan: #213 install and test on every supported Python

Branch `build/213-python-versions` from `main` (3a4dee8). The maintainer's local changes (`.vscode/settings.json`,
`deploy/ansible/ansible.cfg`, untracked `.demo`, `demo`, `config.rri-mtest.yaml.local`) stay in the working tree and
are never staged.

## Findings (evidence)

- F1 `pip install -r requirements-dev.txt` fails on Python 3.14 (macOS report in #213): `rpds-py==0.23.1` and
  `watchfiles==1.0.4` have no cp314 wheels, and building them stops in PyO3 0.23 (max 3.13).
- F2 `lxml`, `MarkupSafe`, `PyYAML` and `uvloop` have no cp314 wheels at their pins and are built from source.
- F3 First releases with macOS cp314 wheels (PyPI): rpds-py 0.26.0, watchfiles 1.1.0, MarkupSafe 3.0.3, PyYAML 6.0.3,
  uvloop 0.22.1, lxml 6.0.1.
- F4 Supported Pythons on 2026-11-20 (endoflife.date): 3.11, 3.12, 3.13, 3.14, 3.15; 3.10 ended 2026-10-01.
- F5 Only 3.11 is used anywhere (the Docker images); the devcontainer has 3.11 only, Docker is available.
- F6 Old pins in `python:<v>-slim` (no compiler): 3.11-3.13 pass, 3.14 and 3.15 fail to install (lxml 5.3.1 first).
- F7 With wheels for 3.14/3.15 (manylinux x86_64): 3.14 fails 4 tests in xsdata 25.7 (`XmlContextError: Failed to
  detect the declared class`), fixed by 26.1; 3.15 fails to import typing_extensions 4.12.2
  (`typing.no_type_check_decorator`), fixed by 4.14.0; then `yaml.CSafeLoader` is missing, because PyYAML 6.0.3 has no
  cp315 wheel and is built without libyaml (`src/rpp/http/app.py`).
- F8 xsdata 26.1 generates the RRI models in another style (kw_only, required fields): not regenerated, #214.

## Decisions (maintainer, 2026-11-20)

- D1 Bump `rpds-py` and `watchfiles` (the failure), and `MarkupSafe`, `PyYAML`, `uvloop` (no source builds on 3.14).
  `lxml` 5 -> 6 is not part of it unless a supported Python needs it.
- D2 A short set of existing unit tests, marked `pyversions`, one per native or version-sensitive dependency.
- D3 Run by a local Docker script over every supported Python, and by a GitHub Actions workflow that calls it.
- D4 Local changes on `main` are left in the working tree, never committed.
- D5 The lowest pins with wheels for both 3.14 and 3.15: lxml 6.1.2, MarkupSafe 3.0.4, PyYAML 6.0.3 (no cp315 wheel
  exists), rpds-py 2026.5.1, uvloop 0.23.0, watchfiles 1.2.0; and xsdata 26.1, typing_extensions 4.14.0 (F7). lxml is
  bumped because 3.14 and 3.15 need it (D1).
- D6 The proxy loads the OpenAPI document with `SafeLoader` where `CSafeLoader` is missing.

## Tasks

- [x] Marker `pyversions` on 8 tests in 6 files; the script; old pins fail on 3.14 and 3.15 (F6)
- [x] Bump the pins (D5), the CSafeLoader fallback (D6); every supported Python passes
- [x] GitHub Actions workflow calling the script
- [x] Docs: supported Pythons and the check (README, testing.project.md, process.project.md)
- [x] Checks: lint-imports (29 kept), unit tests (2904 passed), MTEST reachable, smoke in every environment (190
  passed, 440 skipped by selectors or missing rri-local credentials), the script on 3.11-3.15 (all pass)
- [x] Draft PR #215; the workflow passes on GitHub (3.11-3.15)
- [~] Maintainer review; a run of the install on macOS with 3.14 by the reporter
- [ ] Before merge: `git rm` this plan; release the mutex

## Open questions

- None.
