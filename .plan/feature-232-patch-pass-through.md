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

- [~] T1 `BackendProfile.informational_profiles`, start-up check, `PresetSchemas` scopes from the checked profiles only
- [ ] T2 Configs: generic profiles, `config/backends/epp.yaml`, deployment templates, `config/README.md` if needed
- [ ] T3 Facts `update.*` in `config/common.yaml` and every backend
- [ ] T4 Unit tests for both settings
- [ ] T5 Integration cases: the 8 cases select by the facts; the #192 profile cases select on the profile being checked
- [ ] T6 Docs: architecture.project.md, testing.project.md
- [ ] T7 Checks: lint-imports, unit, MTEST reachability, smoke
- [ ] T8 Draft PR
- [ ] Before merge: `git rm` this plan; release the mutex

## Open questions

- RRI's `update.*` facts: from what the derived update does, to be confirmed on MTEST.
