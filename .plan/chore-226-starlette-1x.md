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

- Accept `Vary: Origin` (a wire change, rule 4): tests check that `Accept` is a member of `Vary`, the cases state
  `"Accept, Origin"`, documented in architecture.project.md.
- #229: marshmallow stays on 3.x (3.26.2); GitHub Actions to v7 and pinned to digests; CI Python stays 3.11.

## Tasks

- [~] T1 (#226) `starlette==1.10.0`, `.trivyignore` without the two CVEs, `Vary` expectations, docs
- [ ] T2 Checks: lint-imports, unit, MTEST reachability, smoke
- [ ] T3 (#229) the dashboard's updates (marshmallow 3.26.2, actions v7 pinned, Python 3.11)
- [ ] T4 Checks: lint-imports, unit, `./test_python_versions.sh`, full run `pytest -n 4`
- [ ] T5 Draft PR; issue for marshmallow 4 blocked by dataclasses-json
