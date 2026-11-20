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

## Decisions (maintainer, 2026-11-20)

- D1 Bump `rpds-py` and `watchfiles` (the failure), and `MarkupSafe`, `PyYAML`, `uvloop` (no source builds on 3.14).
  `lxml` 5 -> 6 is not part of it unless a supported Python needs it.
- D2 A short set of existing unit tests, marked `pyversions`, one per native or version-sensitive dependency.
- D3 Run by a local Docker script over every supported Python, and by a GitHub Actions workflow that calls it.
- D4 Local changes on `main` are left in the working tree, never committed.

## Tasks

- [~] Marker `pyversions` on ~6 tests; the script; run it on the old pins (expected: 3.14 and 3.15 fail)
- [ ] Bump the pins (D1) until every supported Python passes; record the versions
- [ ] GitHub Actions workflow calling the script
- [ ] Docs: supported Pythons and the check (README, testing.project.md, process.project.md)
- [ ] Checks: lint-imports, unit tests, smoke (`epp-docker`), the script on every version
- [ ] Draft PR
- [ ] Before merge: `git rm` this plan; release the mutex

## Open questions

- None.
