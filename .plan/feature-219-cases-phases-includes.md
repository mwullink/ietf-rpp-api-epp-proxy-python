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

## Design (accepted 2026-11-21, answers to Q1 to Q4 below)

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

## Decisions

- D1 (Q1) Superset per include: each include asserts the union of what its uses asserted (201 `01000`,
  `application/rpp+json`, `@type`, id or name; a domain's status, registrant, contacts, `spClientId`, `repositoryId`
  by selector; a request contact's `uriTemplate`, `spClientId`). A setup step only gains assertions, never loses one.
- D2 (Q2) `domain_update/test30` and `test31`: the second part (host objects, epp-docker only) is independent and no
  other case covers it, so it is split into `test70-put_of_host_objects_by_another_client` and
  `test71-patch_of_a_host_object_by_another_client`, with the case-level `when` the steps had.
- D3 (Q3) The `Setup: ` / `Cleanup: ` marker is dropped from the comments; the rest of the comment stays.
- D4 (Q4) Full before/after runs in every environment with credentials, MTEST included.
- D5 Left as inline setup or teardown steps (single uses, or the subject of the case): the preset headers of
  `preset_signalling_header/test1`, `preset_signalling_media_type/test1`, `test8`; the draft example domains of
  `draft_patch/test1`, `test3` (they send and assert `processes`); the transfer requests in `message/test6`'s setup;
  `draft_contact/test6` (contact delete), `draft_host/test6` (host delete).

- D6 (maintainer, 2026-11-21) A case passes `contactInfo` only where its steps rely on the contact's data; a
  change of the wire is allowed where no result relied on the payload. So the 55 contacts of 40 cases that are only a
  domain's contacts, or a contact deleted or transferred, take the default card; the 24 contact updates on the full
  John Doe card use `create_full_contact`; 22 contact updates (and `draft_contact/test5`) keep their own card, which
  their steps change or read back. Compare with `--contact-info`: the 40 cases differ only in the setup contacts'
  `contactInfo`; none of their test steps names a member of a contact card.

## Results

- R1 Converter (scratch `convert.py`): 372 files changed; include uses: `create_contact` 336, `create_domain` 138,
  `create_host` 124, `delete_domain` 76, `create_request_contact` 31, `cancel_transfer` 17; 11 steps inline (D5).
- R2 Compare (scratch `compare.py`, every case in every environment, selects resolved, includes expanded): 0 errors,
  requests identical in order, test steps' responses identical, 808 setup/teardown steps with assertions added.
  A mutation check (a request, a test response and an include changed) is reported by it.
- R3 Every case loads (640) and none runs nowhere.

## Tasks

- [x] T1 Plan, questions to the maintainer
- [~] T2 Baseline full run on the snapshot of `main`'s cases, junit kept in scratch
- [x] T3 Includes and the conversion script; convert all cases
- [x] T4 Compare script: requests and assertions unchanged (apart from D1)
- [x] T5 Docs: testing.project.md (the includes, how a case states its phases)
- [ ] T6 Checks: lint-imports, unit, smoke; after-runs compared to T2
- [ ] T7 Draft PR
