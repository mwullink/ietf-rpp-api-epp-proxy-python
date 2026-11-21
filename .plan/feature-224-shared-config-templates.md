# Plan: #224 shared deployment config templates

Branch `feature/224-shared-config-templates` from `main` (f5a4fd8). The maintainer's local `ansible.cfg` change is stashed
(superseded by an inventory outside the repository with its own `deploy.sh` setting `ANSIBLE_INVENTORY`).

## Findings (evidence)

- F1 `config_template` resolves against `inventory_dir` unless absolute (`roles/rpp_proxy/tasks/main.yml:75`), so an inventory
  outside the repository needs its own copy of the templates.
- F2 A real inventory's `sqlite-demo` template had `rpp_openapi_omit_unheld_objects`/`_unimplemented: true`; the example lacks
  them though `config/backends/sql.yaml:41-42` (its source environment) states them.
- F3 `ANSIBLE_INVENTORY` overrides `inventory =` of `ansible.cfg` (`ansible-config dump`: `DEFAULT_HOST_LIST(env: ANSIBLE_INVENTORY)`).

## Decisions (maintainer, 2026-11-21)

- D1 Templates move to `deploy/ansible/configs/`; inventories reference `"{{ playbook_dir }}/configs/<name>.yaml.j2"`. No role change.
- D2 `ansible.cfg` names no default inventory; `-i` or `ANSIBLE_INVENTORY`.
- D3 README: inventory in a separate private repo; loopback binding as an option next to `docker0`.

## Tasks

- [x] T1 Move the templates, add the two OpenAPI flags to `sqlite-demo`, point the example inventory at them
- [x] T2 `ansible.cfg` without default inventory
- [x] T3 Test `test_deploy_config_templates.py` on the new path; `process.project.md#configurations`
- [x] T4 `deploy/README.md`
- [x] T5 Checks: lint-imports, unit tests, smoke; `ansible-lint`, `--syntax-check`, image build; the path renders in Ansible — lint-imports 29 kept; unit 2932 passed; smoke 190 passed, 440 skipped; ansible-lint 0 failures; syntax-check ok; image built; the example inventory renders the three templates through a local Ansible run
- [x] T6 Draft PR; then the deployment repo uses the shared templates and drops `configs/` — deployment repo: playbook_dir paths, configs/ removed

## Open questions

None.
