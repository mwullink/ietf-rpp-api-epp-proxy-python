# Plan: Renovate, weekly CI and Trivy

Branch `chore/renovate-weekly-ci`.

## Decisions (maintainer, 2026-11-21)

- D1 A new workflow `ci.yml` runs `lint-imports` and the unit tests, on every PR, push to `main` and weekly; the
  Python-versions workflow runs weekly too.
- D2 Renovate runs weekly, groups the non-major updates, automerges them; nothing younger than 24 hours.
- D3 Trivy in CI.

## Findings (evidence)

- F1 The unit tests and `lint-imports` pass in a clean clone without `.env` (2932 passed, 29 contracts kept).
- F2 Trivy 0.69.3 `fs` on `requirements.txt`: 45 HIGH/CRITICAL with a fix in 8 pins (GitPython 29, urllib3 6,
  python-multipart 3, starlette 3, certifi, h11, setuptools, anyio 1 each). Starlette's fixes are in 1.x (major).
- F3 Trivy misconfig: only DS-0002 (root user) on `.docker/Dockerfile`, the development image; skipped in `ci.yml`.
- F4 The Renovate validator could not be run here (denied); `renovate.json` is checked as JSON only.

## Tasks

- [x] renovate.json
- [x] ci.yml (checks + Trivy), weekly schedule on python-versions.yml
- [x] docs: process.project.md, testing.project.md
- [~] Decide how Trivy treats F2 (it fails CI on main, and blocks every automerge)
- [ ] `./test_python_versions.sh`
- [ ] Draft PR

## Open questions

- Q1 F2: fix the pins here, ignore, or make Trivy report-only?
