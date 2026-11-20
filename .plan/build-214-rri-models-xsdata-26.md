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
  MTEST show it.

## Decisions (maintainer, 2026-11-20)

- D1 Commit the regenerated models as generated; pass `value=EmptyType.VALUE` in `rri_queue_read` and
  `rri_queue_delete`; drop the warning of `generate_rri_models.sh`.
- D2 Besides the checks, the full `rri-mtest` integration suite runs (F5).
- D3 Test runs show their progress in the chat.

## Tasks

- [x] Regenerate; the 3 failing tests (F2); the queue fix
- [~] Checks: lint-imports, unit tests, smoke (MTEST reachable first), test_python_versions.sh
- [ ] Full `rri-mtest` run
- [ ] Draft PR
- [ ] Before merge: `git rm` this plan; release the mutex

## Open questions

- None.
