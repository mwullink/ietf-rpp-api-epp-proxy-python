# Plan: #218 harness phases, includes, until-loops, a queue mutex; drain the message queue

Branch `feature/218-harness-phases-includes-loops` from `main` (591fce6). #219 (rework of all cases) follows.

## Findings (evidence)

- F1 The runner ([file_cases.py](../tests/integration/file_cases.py) `run_case`, `endpoint_test` of
  [integration_api_test.py](../tests/helper/integration_api_test.py)) resolves the placeholders of the whole case once,
  before the first step: `{unique_cltrid}` is one value per occurrence in the file. A step repeated by a loop would
  resend its clTRID, which the EPP test server refuses with `2400` (testing.project.md, Backend).
- F2 `pyproject.toml` runs with `-p no:warnings` and ignores `UserWarning`: a `warnings.warn` never reaches the report.
- F3 Pytest reports an exception of `Item.setup()` as an error, of `runtest()` as a failure, and runs `teardown()` after
  either. xdist forwards report `sections` and `user_properties` to the controller.
- F4 Cases that request a transfer: `contact_transfer/` 18, `domain_transfer/` 14, `planet_transfer/` 14,
  `domain_transfer_ext/` 6, `draft_contact/` 5, `draft_domain/` 5, `planet_message/` 2, `message/` 1,
  `planet_delete/` 1, `satellite_delete/` 1. Queue readers: `message/`, `planet_message/`.
- F5 The EPP test server approves a pending transfer after 5 minutes and queues messages then. A case that ends with a
  transfer pending puts a message into a queue minutes after it released any mutex.
- F6 Probe (T1, 2026-11-21, GET /messages): MTEST queues messages on its own, which no mutex holds back. Head of `a`
  (2936 queued): `serviceNoticeMessage` "RRI domainStatusUpdate: t5-domain-lifecycle-….de", a status change of a
  domain a case created; head of `b` (9 queued): "RRI contactDelete: DENIC-99995-SAKA-AUTODNS-TEST", DENIC's
  housekeeping of a contact not of the suite. EPP test server: `a` 1529 queued, head a contact `transferRequestMessage`
  (pending, auto-approve 5 minutes later); `b` empty.
- F7 Drain cost: one message is a GET and a DELETE. The pacer gives each of N workers 1/N of
  `rpp_requests_per_minute` (MTEST 25): with `-n 4` a request every 9.6 s, the 2936 messages of MTEST `a` take about
  16 hours, about 4 hours at the full 25 a minute. Every MTEST run creates domains whose `domainStatusUpdate` arrives
  later, so each run's setup drains the previous run's notices.

## Design (accepted 2026-11-21)

### Case file

```json
{
  "test_id": "...",
  "exclusive": ["message_queue"],
  "setup":    [ items ],
  "steps":    [ items ],
  "teardown": [ items ]
}
```

- `steps` stays the phase of the operation under test, so the 685 files load unchanged; `setup`, `teardown` and
  `exclusive` are optional.
- An item is a step as today, an include, or a loop. `when` works on each of them; `select`, `wait`, `capture`,
  placeholders and captures work in every phase. Captures are one namespace across the phases.

### Includes

- `test_case_data/_includes/<name>.json`:
  `{"comment": "...", "parameters": {"registrar": {"comment": "..."}, "suffix": {"comment": "...", "default": "X"}}, "steps": [items]}`.
- Used as `{"comment": "...", "include": "drain_queue", "with": {"registrar": "a"}}`, optionally with `when`.
- `{param:name}` is replaced when the case loads; a whole-string `{param:name}` takes any JSON value. The other
  placeholders in a value are resolved later as usual.
- An include may use includes. A load error names the include and the parameter for: an unknown include, a missing
  parameter without default, an unknown parameter in `with`, a `{param:x}` the include does not declare, a cycle.
- A capture inside an include is available to the later steps of the case.

### Until-loop

- `{"comment": "...", "loop": [items]}`; exactly one step in it has `"until": <response matcher>` (the form of
  `response`). After that step's response has passed its `response`, the loop ends when it also matches `until`; the
  step's `capture` is then not taken. No maximum.
- Placeholders are resolved per step when it runs (F1), so `{unique_cltrid}` is new each iteration. `{random_name}`
  and `{test_start}` keep one value per case, as today.

### Phases and the report

- `Case.setup()` takes the mutexes, runs the run setup of the environment if not done yet, then the case's `setup`.
  A failure is a pytest **error**. `runtest()` runs `steps`: a failure is a **failure**. `teardown()` runs `teardown`
  always, also after an error or failure, step by step: a failing step is recorded and the next runs; a failing step
  inside a loop ends that loop. It never raises.
- A teardown failure is a report section of the case and a `teardown warnings` section in the terminal summary
  (F2, F3), so it shows with xdist too.
- Every failure message starts with where it happened: `setup[2] > include drain_queue[0] > loop iteration 7`.

### Run setup and teardown

- `test_case_data/_run.json`: `{"setup": [items], "teardown": [items]}`, run per environment.
- Run setup: once per environment and run, across xdist workers (a file lock and a marker in a directory of the
  run, keyed by xdist's `testrun_uid`), by the first case of that environment that runs. If it fails, every case of
  that environment is an error naming it.
- Run teardown: in the process that ends the run (the xdist controller, or the only process), for each environment
  whose run setup ran; a failure is a line in the `teardown warnings` summary.

### Mutex

- `"exclusive": [names]`: a file lock per run, environment and name, taken in `setup()` before anything and released
  at the end of `teardown()`. Several names are taken in sorted order.

### Applying it (scope b of #218)

- `_includes/drain_queue.json` (parameter `registrar`): a loop of GET `/messages` with `until` RPP-Code `01300`, else
  capture `0.id` and DELETE it.
- `_run.json`: setup and teardown drain registrars `a` and `b`.
- Readers (`message/`, `planet_message/`): `exclusive: ["message_queue"]`, setup drains the queues they read, and
  they assert the exact message of their own action (no `any_of`, `RPP-Queue-Size` exact).
- Producers (F4): `exclusive: ["message_queue"]`; their teardown cancels a transfer that may still be pending (F5), as
  a best-effort step whose failure is a warning.
- Testing docs: the new format in `docs/agents/testing.project.md` (Test data format).

### Code

- Harness modules in `tests/helper/`, one class per file: include expansion, the step runner (steps, loops, phases,
  per-step placeholders), the run lock. `conftest.py` and `file_cases.py` call them.
- Harness tests in `tests/unit/` with `pytester`: an inner pytest over a temporary case directory against
  `sqlite-demo` (no server, no credentials), for error / failure / pass-with-warning, include and loop behaviour and
  load errors; the case directory is given by `RPP_TEST_CASE_DATA` (default `test_case_data`). The lock is tested on its
  own with two processes.

- F8 `planet_message/` already asserts exact messages: its registrars `c` and `d` read queues of a database in memory
  per worker, which no other case and no other worker writes. Left as it is; the planet transfer cases need no mutex
  either, as no reader of the queues of `a` and `b` runs on SQLite (`message/` needs contacts).
- F9 EPP test server, 2026-11-21: after the drain the head of `a` is the transfer request of `message/test6` itself,
  `RPP-Queue-Size` 1; its process is a `domainTransferProcess`, `objectType` `domainName`. The first run drained the
  1529 messages of `a` in its run setup.

## Decisions

- D1 (maintainer, in #218) per case and per run; until-loops without maximum; teardown warnings; setup errors; drain
  MTEST; a mutex for readers and producers; exact assertions.
- D2 (maintainer, 2026-11-21) the design above is accepted.
- D3 (maintainer, 2026-11-21) Q1: producers' teardown cancels a transfer that may still be pending.
- D4 (maintainer, 2026-11-21) Q2 (F6): a reader acks the heads that are not its own until its own message is the head,
  and asserts that message exactly; the exact `RPP-Queue-Size` only where the server queues nothing on its own (a new
  environment fact).
- D5 (maintainer, 2026-11-21) Q3 (F7): the run setup drains at the registrar's full rate, as the other workers of the
  environment wait for it; the MTEST backlog is drained once by hand (a throwaway script outside the repository, 25
  requests a minute, one session) while the code is written.

## Tasks

- [x] T0 Design accepted by the maintainer
- [x] T1 Probe MTEST and the EPP test server: which operations queue messages, and whether any arrive later (F5, F6)
- [x] T2 Failing harness tests (pytester), stubs
- [x] T3 Include expansion and load checks
- [x] T4 Step runner: per-step placeholders, loops, phases, report sections
- [x] T5 Run setup/teardown and the mutex
- [~] T6 `_includes/drain_queue.json`, `_run.json`; readers and producers
- [ ] T7 Docs: testing.project.md
- [ ] T7b One-time MTEST drain (running since 2026-11-21)
- [ ] T8 Checks: lint-imports, unit tests, smoke (MTEST reachable first)
- [ ] T9 Draft PR
- [ ] Before merge: `git rm` this plan; release the mutex

## Open questions

- None.
