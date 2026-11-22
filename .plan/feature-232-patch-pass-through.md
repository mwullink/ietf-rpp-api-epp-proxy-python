# Plan: #232 PATCH passed through to EPP; informational profiles; add/remove facts

Branch `feature/232-patch-pass-through` from `feature/219-cases-phases-includes` (c231508, PR #231): stacked on #231,
the draft PR targets that branch and is retargeted to `main` once #231 is merged.

## Findings

- Reproduced at c231508: the 8 cases of the issue fail on epp-docker (`02308` "no element matches" for
  `domain_update/test1` and others), 48 skipped.
- `contact_patch`, `host_patch`, `domain_patch` `rpp_to_model` return None whenever `profiles_apply()` (#192), so
  every PATCH under `epp-compatible` reads and applies the patch itself.
- `PresetSchemas` builds a `SchemaScope` per preset from `item.applicable`; the Preset Schema document composes the
  same profiles. `rpp_protocol_config` is test facts only (the proxy keeps but does not use it).

## Decisions (maintainer, 2026-11-22)

- Whether the proxy checks a profile is configuration, per profile: `rpp_backend_profile.informational_profiles`, the
  keys of the profiles the server checks itself. Default `[]` (every profile is checked by the proxy).
- An informational profile is not checked by the proxy on any request (create, PUT, PATCH); it stays advertised
  (discovery, the Preset Schema, `/profiles/{id}`).
- A profile the proxy checks keeps the read of #192 on a PATCH (the whole resulting object is checked).
- epp-docker: `informational_profiles: [epp-compatibility]`; RRI has no profiles; the SQLite environments unchanged.
- Facts `rpp_protocol_config.update.add_existing_supported` and `remove_absent_supported`.

## Tasks

- [x] T1 `BackendProfile.informational_profiles`, start-up check, `PresetSchemas` scopes from the checked profiles only
- [x] T2 Configs: generic profiles, `config/backends/epp.yaml`, `deploy/ansible/configs/epp.yaml.j2`, README
- [x] T3 Facts `update.*`: `config/common.yaml` (null), `config/backends/epp.yaml` (false/true), `config/protocols/rri.yaml`
  (true/true: RRI updates are applied to the object read, `<object>_application.apply` keeps an item once)
- [x] T4 Unit tests (`test_preset_profile_constraints_wire.py`): both settings, PATCH without a read, start-up refusals
- [x] T5 Integration cases: `host_update/test32`, `limits_host/test12`, `contact_update/test6`, `test19` select by the
  facts; the 8 profile cases of #192 (`contact_create/test18/23/25`, `domain_restore/test8/9`, `limits_contact/test10/21/23`)
  select on `profile.informational_profiles`. The 8 cases of the issue and these 8 pass on epp-docker (16 passed).
- [x] T6 Docs: architecture.project.md, testing.project.md
- [x] T7 Checks (2026-11-22): lint-imports 29 kept; unit 2988 passed; MTEST reachability passed, so the smoke run covers
  MTEST: smoke 190 passed, 440 skipped
- [x] T8 Draft PR #235 (base feature/219-cases-phases-includes)
- [x] T9 (maintainer, 2026-11-22) A second environment over epp-docker that checks the profile: `epp-docker-checked`
  (config includes `epp-docker.yaml`, `informational_profiles: []`; descriptor includes `epp-docker.yaml`). Harness:
  a descriptor's `server` (default its name) keys the mutex, the run setup and teardown, and the worker limit
  (workers x environments of the server <= `max_workers`); `{random_name}`/`{random_id_10}` per process and
  environment, so twins over one server never meet. Cases that differ select on `profile.informational_profiles`.
  Full run of `epp-docker-checked` alone (-n 8): 8 failed, 457 passed, the 8 cases of the issue. Now: the adds
  (`host_update/test32`, `test36`, `limits_host/test12`) are 200 and the removes of an absent status
  (`contact_update/test6`, `test19`) 422 `02308` where the proxy checks the profile; `domain_update/test1`, `test3`,
  `test4` are skipped there until #234 (contact ids are read back in upper case too, commented on #234). The 16
  cases and `message/` on both environments together (-n 4): passed; -n 8 over both is refused by the worker limit.
- [x] T10 Checks (2026-11-22): lint-imports 29 kept; unit 2991 passed; smoke (every environment, MTEST and
  epp-docker-checked included) 232 passed, 488 skipped
- [ ] Before merge: `git rm` this plan; release the mutex

## Findings during the work

- With the profile checked on epp-docker, the read path fails `domain_update/test1`, `test3`, `test4` because a
  `match` on `hostName` is case-sensitive and EPP reads host names in upper case: #234 (not fixed here).
