# Plan: Renovate, weekly CI and Trivy

Branch `chore/renovate-weekly-ci`.

## Decisions (maintainer, 2026-11-21)

- D1 A new workflow `ci.yml` runs `lint-imports` and the unit tests, on every PR, push to `main` and weekly; the
  Python-versions workflow runs weekly too.
- D2 Renovate runs weekly, groups the non-major updates, automerges them; nothing younger than 24 hours.
- D3 Trivy in CI, failing on HIGH/CRITICAL with a fix.
- D4 F2: fix the pins here, drop the unused GitPython, ignore Starlette's 1.x-only CVEs in `.trivyignore` (#226).

## Findings (evidence)

- F1 The unit tests and `lint-imports` pass in a clean clone without `.env` (2932 passed, 29 contracts kept).
- F2 Trivy 0.69.3 `fs` on `requirements.txt`: 45 HIGH/CRITICAL with a fix in 8 pins (GitPython 29, urllib3 6,
  python-multipart 3, starlette 3, certifi, h11, setuptools, anyio 1 each). Starlette's fixes are in 1.x (major).
- F3 Trivy misconfig: only DS-0002 (root user) on `.docker/Dockerfile`, the development image; skipped in `ci.yml`.
- F5 GitPython, gitdb and smmap: nothing in `src/`, `tests/` or the installed packages imports or requires them.
- F6 New pins (each released before 2026-11-20): urllib3 2.8.0, python-multipart 0.0.34, certifi 2026.10.23, h11 0.16.0
  with httpcore 1.0.9 (h11<0.15 before), setuptools 84.2.1, anyio 4.16.0 with typing_extensions 4.16.0, starlette
  0.52.1 (last 0.x). Trivy with `.trivyignore`: 0 findings.
- F7 Checks: lint-imports 29 kept; unit 2932 passed; `./test_python_versions.sh` passed on 3.11–3.15; smoke 158 passed,
  32 failed, all `rri-mtest` with 401; the deploy image builds.
- F8 MTEST pending: the one-case check fails with `RRI login refused: 83000000010` (login refused from here). Handed
  over to the maintainer.
- F4 The Renovate validator could not be run here (denied); `renovate.json` is checked as JSON only.

## Tasks

- [x] renovate.json
- [x] ci.yml (checks + Trivy), weekly schedule on python-versions.yml
- [x] docs: process.project.md, testing.project.md
- [x] Decide how Trivy treats F2 (D4)
- [x] Pins, `.trivyignore`, issue #226
- [x] lint-imports, unit tests, `./test_python_versions.sh`, smoke (MTEST pending, F8)
- [~] Draft PR

