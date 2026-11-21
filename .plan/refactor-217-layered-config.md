# Plan: #217 layered configuration with local overrides

Branch `refactor/217-layered-config` from `main` (9e4627f), in its own worktree (`.claude/worktrees/217-layered-config`)
at the maintainer's request: the main checkout holds #214 and its mutex. This worktree has its own `.agent-sync.yml`;
`.env` and `.venv` are links to those of the main checkout.

## Findings (evidence)

- F1 `load_settings` already reads `<name>.local.yaml` next to the config and replaces top-level keys (a mapping whole,
  `tests/unit/test_config_local_override.py`); `*.local.yaml` is in `.gitignore`.
- F2 Test descriptors are read as single files (`tests/helper/test_environment.py::_descriptor`); `environment_names()`
  globs `environments/*.yaml`, so a `*.local.yaml` there would count as an environment.
- F3 Repetition: `sqlite-demo{,-bound,-extended,-inherit}.yaml` (114 lines each) differ only in `config:`/`preset:`;
  `rri-mtest`/`rri-local` descriptors in ~10 lines, their configs in host and TLS verification; the demo configs share
  all but extensions, presets and signalling.
- F4 `null` is a value in the descriptors' facts ("the field is not there, or the limit is not known", e.g. rri-local
  `failed_dns_status: null`); `env_fact` tells a missing leaf (KeyError) from a null one.
- F5 `src/config.yaml` is a tracked link to `../config.yaml`; `.docker/Dockerfile` copies `config.yaml` to `/config.yaml`
  for it; `deploy/docker/Dockerfile` removes `/app/config.yaml` and sets `RPP_CONFIG_FILE=/config/config.yaml`.
- F6 `test_deploy_config_templates.py` finds the source of a template by `made from (config[\w.-]*\.yaml)` in its header
  and compares top-level keys with the raw YAML of that file.

## Decisions (maintainer, 2026-11-20, on #217)

- D1 Deep merge everywhere, `.local.yaml` included: maps merge, lists and values replace.
- D2 Layout `config/{protocols,backends,environments}/`; protocol = client settings of the wire protocol (epp, rri,
  direct), backend = what a registry server holds (EPP-server-docker, DENIC, the demo SQL database).
- D3 Root `config*.yaml` and `src/config.yaml` are removed, no stubs.
- D4 A startup warning for an unknown `rpp_*` key, in this issue.
- D5 (agent, from F4; to confirm) `null` replaces like any value, so a descriptor can state a null fact over a shared one.
  In the app config a top-level key whose resolved value is `null` counts as absent, which is how a `.local.yaml` unsets
  a key. The issue text "null unsets a key" holds for the app config.
- D6 (agent) The default config, without `RPP_CONFIG_FILE`, is `config/environments/epp-docker.yaml` resolved from
  `src/settings/` (`parents[2]`), not the working directory; the dev image copies `config/` to `/config` for it.
- D7 (agent) Includes and local files of every layer are resolved by one module, `src/settings/layered_yaml.py`, which
  the test helper uses for the descriptors too.

## Tasks

- [x] Loader `settings/layered_yaml.py` (include, deep merge, `.local.yaml` per layer, cycle, missing include,
      provenance of each top-level key) and its unit tests; `load_settings` uses it, warns about unknown `rpp_*` keys
- [x] `config/` tree; equivalence check: each new environment resolves to the same `Settings` as its old root file
      (all 7 equal, checked with a script before the old files were removed)
- [x] Descriptors: `environments/common/rri.yaml`, `sqlite-demo-*` include `sqlite-demo.yaml`, `config:` defaults to
      `config/environments/<name>.yaml`, `.local.yaml` skipped by `environment_names()`; each resolved descriptor
      equals the old file with the new `config` (all 7)
- [x] Remove root `config*.yaml`, `src/config.yaml`; update tests, Dockerfiles, deploy template headers and their test;
      `.dockerignore` keeps `*.local.yaml` (and `.env`) out of the images, as the dev image now copies `config/`
- [x] Docs: README, config/README.md, process.project.md, architecture.project.md, testing.project.md,
      security.project.md, docs/testing/backend-limits.yaml, .gitignore comment (docs/rri/refactoring.md is the
      historic design and keeps its old example)
- [~] Checks: lint-imports (29 kept), unit tests, smoke (MTEST reachable first), docker build of both images;
      ansible-lint / --syntax-check: not installed here (only comments of the templates changed, which the unit test
      renders)
- [ ] Draft PR
- [ ] Before merge: `git rm` this plan; release the mutex; maintainer moves `config.rri-mtest.local.yaml` to
      `config/environments/rri-mtest.local.yaml`

## Open questions

- D5 to confirm.
