# Plan: #214 the RRI models generated with xsdata 26

Branch `build/214-rri-models-xsdata-26` from `main` (9e4627f). The maintainer's local changes (`.vscode/settings.json`,
`deploy/ansible/ansible.cfg`, untracked `.demo`, `demo`, `config.rri-mtest.yaml.local`) stay in the working tree and
are never staged.

## Findings (evidence)

- F1 `generate_rri_models.sh` with xsdata 26.1 rewrites the 8 files of `src/registry_adapter/rri/xml/generated/`
  (+488/-593): `@dataclass(kw_only=True)`, `from __future__ import annotations`, `None | X`, and an element or
  attribute the XSD requires has no default. xsdata 26.1 has no option for the old style (CLI flags, `init-config`).
- F2 With them the unit tests give 3 failed, 2901 passed: `test_rri_adapter.py` queue read, empty queue and queue
  delete, `TypeError: QueueRead.__init__() missing 1 required keyword-only argument: 'value'` (and `Delete`).
- F3 `value` is the simple content of `readType`/`deleteType`, `msg:emptyType`, whose only value is ""
  (`docs/rri/xsd/message-5.0.xsd`). `QueueRead(value=EmptyType.VALUE)` serializes as the old `QueueRead()` did:
  `<queue-read/>`, `<delete msgid="42"/>`.
- F4 A static scan of every construction of a generated class in `registry_adapter/rri` and `tests` finds no other
  missing required field; the constructions with `**kwargs` are covered by the passing unit tests.
- F5 Risk: a reply without an element the XSD requires parsed with `None` before and may fail now; only replies from
  MTEST show it. The full MTEST run shows no such reply (F7).
- F6 A first full MTEST run was void: `config.rri-mtest.local.yaml` (untracked, not from this branch) appeared during
  it and pointed rri-mtest to a local RRI at 172.17.0.9 (connection refused). Renamed to `.off` for the rerun on the
  maintainer's word, restored afterwards.
- F7 Full `rri-mtest` run: 249 passed, 2 failed, 4215 skipped. Both failures also fail with main's models and code:
  `limits_contact/test16-email_without_at` (500 from `83000000004`, #139) and
  `preset_signalling_media_type/test2-base_refuses_the_rri_specifics` (400 `02001` where the case expects 501, #221).

## Decisions (maintainer, 2026-11-20)

- D1 Commit the regenerated models as generated; pass `value=EmptyType.VALUE` in `rri_queue_read` and
  `rri_queue_delete`; drop the warning of `generate_rri_models.sh`.
- D2 Besides the checks, the full `rri-mtest` integration suite runs (F5).
- D3 Test runs show their progress in the chat.

## Tasks

- [x] Regenerate; the 3 failing tests (F2); the queue fix
- [x] Checks: lint-imports (29 kept), unit tests (2904 passed), MTEST reachable, smoke in every environment (190
  passed, 440 skipped), test_python_versions.sh (3.11-3.15 pass)
- [x] Full `rri-mtest` run (F7)
- [x] Draft PR #222
- [~] Maintainer review
- [ ] Before merge: `git rm` this plan; release the mutex

## Open questions

- None.
