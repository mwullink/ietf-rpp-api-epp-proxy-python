# Plan: #217 layered configuration, part 2: the facts in the configuration

Same branch `refactor/217-layered-config` and PR #220 (back to draft), at the maintainer's request (2026-11-21). Part 1
(layers, local files, descriptors) is in f61a5b8; its plan was removed in 107b890.

## Findings (evidence)

- F1 The descriptors' `facts` are what the registry does where the protocol leaves the choice to the server; the cases
  select on them as `env.<path>` (tests/helper/selectors.py). `facts.bugs` are a server's defects.
- F2 `test_every_environment_states_the_same_facts`: every environment states every fact path, null when not known.
- F3 The sqlite-demo facts are a copy of epp-docker's, although the demo backend holds no domains or contacts.
- F4 Baseline before the change: the merged facts of every environment (scratchpad facts-before.json) and the
  collection outcome of every case in every environment, 4466 items: 1057 run, 3409 skipped with their reasons
  (skips-before.txt).

## Decisions (maintainer, 2026-11-21)

- D1 Continue on this branch and PR.
- D2 The facts go into the configuration under the key `rpp_protocol_config`, known to the proxy (no warning) and
  loaded as a mapping it does not use. The test helper merges the descriptor's `facts` over it, so a descriptor keeps
  only singular exceptions: the bugs. The selectors stay `env.<path>`.
- D3 Layers: `common.yaml` every path null with the explanations once; `protocols/epp.yaml` what RFC 5730/5731 fix;
  `protocols/rri.yaml` DENIC's rules (RRI is DENIC's protocol only); `backends/epp.yaml` EPP-server-docker's policy;
  `backends/sql.yaml` the session fact; `environments/rri-mtest.yaml` and `rri-local.yaml` what is theirs alone.
- D4 The sqlite-demo domain and contact facts become null.

## Tasks

- [x] `rpp_protocol_config` in Settings and KNOWN_KEYS; the test helper merges it with the descriptor's facts
- [x] Move the facts into the layers; descriptors keep `bugs` only. environments/common/rri.yaml stays: it holds what rri-mtest and rri-local share of the run (preset, workers, regacc, unknown user, bugs)
- [x] Verify: merged facts equal the baseline but for 35 sqlite-demo nulls per demo environment; run/skip of all 4466 items identical (sqlite skips name more unmet facts). A null fact now meets no min/max and has no member (selectors.py), else 6 cases failed to load against the sqlite nulls
- [x] Docs: config/README.md, testing.project.md (facts, selectors), architecture.project.md (the key)
- [x] Checks: lint-imports 29 kept; unit 2932 passed; MTEST reachable; smoke 190 passed, 440 skipped
- [~] PR #220 description; maintainer accepts; ready; `git rm` this plan; release the mutex

## Open questions

- None.
