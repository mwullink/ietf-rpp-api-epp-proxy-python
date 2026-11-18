# Plan: #173 the local RRI environment, merged with main

Branch `csi` of PR #173 (Christian Simmen), pulled and merged with `main` (no rebase), so the contribution stays in the
history. The maintainer's local changes (`.vscode/settings.json`, `deploy/ansible/ansible.cfg`) are stashed
(`pre-#173 local changes`) and popped on `main` at the end; the untracked `config.rri-mtest.yaml.local` is never committed.

## Findings (evidence)

- F1 #190 on main already transfers the domain of `message/test6` by CHPROV with registrant, request contacts and dns, and
  expects `200`/`serverApproved`: the PR's change of that step is superseded.
- F2 Main leaves `RPP-Queue-Size` out of test6's queue delete on RRI by `profile.extensions`; the PR names the defect as
  `bugs.queue_del_no_msgcnt` (#172). A fact a case names must be in every environment (`selectors.env_fact`: `KeyError`).
- F3 The PR's `rri-local.yaml` and `config.rri-local.yaml` were made from an older `rri-mtest`: `profile:` (now `preset:`),
  no preset signalling, presets or default preset, and facts main added since are missing.
- F4 `rri-local` names the MTEST variables (`TEST_RRI_REGACC1`…): a run with MTEST credentials in `.env` would test the
  local RRI too and fail without one.
- F5 The untracked override the maintainer asked for exists already: `load_settings` merges `<name>.local.yaml`, and
  `.gitignore` has `*.local.yaml`. For `config.rri-local.yaml` it is `config.rri-local.local.yaml`.
- F6 The local fake predelegation check passes every create and update (maintainer): `failed_dns_status: null` skips test43
  without the PR's `pdc.pdc_always_true` fact, `update.dns_checked: false` the update cases that need a check.

## Decisions (maintainer, 2026-11-18)

- D1 Merge main into the PR branch, fix on top; no rebase.
- D2 test6 keeps the PR's `bugs.queue_del_no_msgcnt` (true on RRI) instead of the `profile.extensions` selector.
- D3 The host stays `172.17.0.8`; a machine with another one sets it in the untracked `config.rri-local.local.yaml`.
- D4 rri-local: 4 workers, 2000 RPP requests a minute.

## Tasks

- [x] Merge main into `csi` (conflicts to main's versions, test43 back to main's)
- [x] `config.rri-local.yaml` and `rri-local.yaml` from the current rri-mtest ones, own `TEST_RRI_LOCAL_*` variables (F3–F6)
- [x] `bugs.queue_del_no_msgcnt` in every environment, test6's queue delete on it (D2)
- [x] testing.project.md: the local RRI environment and the new bug
- [x] Checks: lint-imports (28 kept), unit tests (2869 passed), smoke: every epp-docker and sqlite case passes; all 32
  failures are rri-mtest, each an RRI LOGIN refused with `83000000010` from this machine (not on the allowlist), not
  this change. rri-local: skipped (no local RRI or `TEST_RRI_LOCAL_*` here), app composes with its config. Pending:
  MTEST and rri-local smoke runs from a machine that reaches them.
- [~] Push to the PR branch, PR description
- [ ] Before merge: `git rm` this plan; pop the stash on `main`; release the mutex

## Open questions

- None.
