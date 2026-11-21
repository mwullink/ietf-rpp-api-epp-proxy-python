# Plan: #219 rework the integration cases to use setup, teardown and includes

Branch `feature/219-cases-phases-includes` from `main` (ecd0392, #218 merged).

## Findings (evidence)

- F1 686 case files in 51 groups (`tests/integration/test_case_data/[!_]*/*.json`). 17 have a `teardown` and 2 a
  `setup` already (#218: the transfer cancels, `message/test1`, `message/test6`).
- F2 The step comments already mark the phases: 629 steps say `Setup:`, 77 say `Cleanup`. Per case the order is
  `S* T+ C*` in 684 files (170 have only test steps). Two files break it: `domain_update/test30` and `test31` are
  `S S T C S S T` (a second scenario after a cleanup).
- F3 The setup and cleanup steps are 706 steps in 171 distinct forms (comment left out, handle suffix, domain name and
  capture names normalised). By operation: contact create 337 uses in 33 forms; domain create 139 in 40; host create
  124 in 80 (58 host names, the ns record and the response vary); domain delete 70 in 5; requestContact create 27 in 5;
  the rest single.
- F4 What varies within one operation is mostly in the request body (contact data, authInfo, registrant, ns records)
  and in **the assertions of the setup step**: of 337 contact creates 160 assert `content_type`, 58 `RPP-Code`, 136
  `body.id`; of 139 domain creates 95 `content_type`, 45 `RPP-Code`, 22 `body.name`; of 124 host creates 42
  `content_type`, 39 `RPP-Code`, 27 `body.hostName`. So an include that keeps every assertion of every case
  unchanged needs the response as a parameter.
- F5 `includes.py` substitutes `{param:…}` in values only, not in keys: a capture name in an include is fixed.

## Design (proposed, awaiting acceptance)

- Phases from the comment markers: the leading `Setup:` steps go to `setup`, the trailing `Cleanup` steps to
  `teardown`, the rest stays in `steps`. A script does it (scratch, not committed), so it is mechanical.
- Includes in `_includes/` per repeated operation, with the varying request parts as parameters:
  `create_contact`, `create_domain`, `create_host`, `delete_domain`, `create_request_contact` (names to be fixed in
  the implementation). Each with `registrar` (default `a`) and the identifiers; the body parts that vary as
  parameters with the most common form as default.
- Verification, `scratch/compare_cases.py`: expands old and new case (includes expanded, phases concatenated) and
  compares the requests and the assertions, step by step, ignoring comments. Every difference is listed.
- Outcomes: a full run per environment before (on `main`) and after, compared from junit (case id → pass, skip,
  fail, error), with an error of a setup counted as the failure it was before.

## Open questions

- Q1 Setup assertions (F4): keep every assertion exactly (response as include parameter, verbose), or one assertion
  set per include (status and `@type`, plus what all its uses share)?
- Q2 `domain_update/test30`, `test31` (F2): only the leading setup and nothing in teardown, the rest stays in steps?
- Q3 Comments: drop the `Setup:`/`Cleanup` marker sentence from the moved steps, since the phase states it?
- Q4 Baseline runs: which environments for the before/after full runs (MTEST full run is long, rate-limited)?

## Tasks

- [~] T1 Plan, questions to the maintainer
- [ ] T2 Baseline full runs on `main`, junit kept in scratch
- [ ] T3 Includes and the conversion script; convert all cases
- [ ] T4 Compare script: requests and assertions unchanged (apart from the accepted differences)
- [ ] T5 Docs: testing.project.md (the includes, how a case states its phases)
- [ ] T6 Checks: lint-imports, unit, smoke; after-runs compared to T2
- [ ] T7 Draft PR
