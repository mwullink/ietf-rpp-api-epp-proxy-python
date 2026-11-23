# Plan: #226 Starlette 1.x; #229 the Renovate dashboard's updates

Branch `chore/226-starlette-1x` from `main` (0d1d35b). Two steps in one PR: Starlette first (smoke run), then the
updates of #229 on top (full run).

## Findings

- Connexion 3.2.0 and 3.3.0 require `starlette>=0.35`, no upper bound; Starlette 1.10.0 installs, `pip check` clean.
- With Starlette 1.10.0: lint-imports 29 kept; unit 2966 passed, 30 failed, all `assert 'Accept, Origin' == 'Accept'`
  (`test_preset_media_type_wire.py`, `test_preset_schemas.py`).
- Cause: Starlette 1.x `CORSMiddleware` adds `Vary: Origin` to every simple response; with `allow_origins=["*"]` and
  `allow_credentials=True` it mirrors the `Origin` (before: only with a cookie). The cases
  `preset_signalling_media_type/test3`–`test9` state `"Vary": "Accept"` too.
- With every Python update of #229 on top: the same 30 failures, nothing else. marshmallow 4 cannot be installed:
  `dataclasses-json` 0.6.7 (latest) requires `marshmallow<4`.

## Decisions (maintainer, 2026-11-23)

- Accept `Vary: Origin` (a wire change, rule 4): the unit tests and the cases state
  `"Accept, Origin"`, documented in architecture.project.md.
- #229: marshmallow stays on 3.x (3.26.2); GitHub Actions to v7 and pinned to digests; CI Python stays 3.11.

## Tasks

- [x] T1 (#226) `starlette==1.10.0`, `.trivyignore` without the two CVEs, `Vary` expectations (unit tests and
  `preset_signalling_media_type` cases: `Accept, Origin`), architecture.project.md
- [x] T2 Checks (2026-11-23): lint-imports 29 kept; unit 2996 passed; MTEST reachability passed, so the smoke run
  covers MTEST: smoke 232 passed, 488 skipped
- [x] T3 (#229) the dashboard's updates (marshmallow 3.26.2; checkout v7.0.1 and setup-python v7.1.0 pinned in both
  workflows; `.docker/Dockerfile` python:3.11-slim pinned to its digest; CI Python 3.11, and Renovate's 3.11 rule
  extended to the `github-actions` manager so it stops proposing 3.15)
- [x] T4 Checks (2026-11-23): lint-imports 29 kept; unit 2996 passed; `./test_python_versions.sh` 3.11–3.15 passed;
  full run `pytest -n 4` (MTEST included): 4492 passed, 3624 skipped (1:31:50)
- [~] T5 Draft PR #240, awaiting the maintainer; issues #241, #242: marshmallow 4 blocked by dataclasses-json; `starlette.testclient` deprecates `httpx`
  (`StarletteDeprecationWarning`: install `httpx2`, `tests/integration/file_cases.py:16`)
