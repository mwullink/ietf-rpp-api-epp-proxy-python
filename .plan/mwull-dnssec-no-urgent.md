# Plan: PR #243, optional EPP attributes at their default are left out

Branch `mwull/dnssec-no-urgent` (PR #243, from mwullink's fork, maintainer edits allowed), based on 0d1d35b. The
maintainer asked to replace the per-field `urgent=None` with the serializer option and to run the full suite.

## Findings

- xsdata 26.10 `SerializerConfig(ignore_default_attributes=True)` leaves out an attribute that is not required and
  whose value equals its default (`XmlVar.is_optional`). The PR's `urgent=None` is no longer needed.
- With the option on, 5 of 192 `tests/unit/*xml*.py` fail, each an attribute now left out: `status lang="en"`
  (contact, domain), `addr ip="v4"` (host), `hostAddr ip="v4"` (domain). `domain:name hosts="all"` (info) is left out
  too, untested. RFC 5730-5733 and 5910 define each default, so the request means the same (wire change, rule 4).

## Decisions (maintainer, 2026-11-25)

- The option is set for every EPP request; pushed to the PR branch. Full run `pytest -n 4` on all backends.

## Tasks

- [~] T1 `ignore_default_attributes=True` in `epp/xml/codec.py`, `urgent=None` removed, tests (the 5 and `urgent`
  absent), architecture.project.md
- [ ] T2 Checks: lint-imports, unit, MTEST reachability, full run `pytest -n 4`
- [ ] T3 Push, PR description
