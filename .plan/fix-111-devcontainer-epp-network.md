# Plan: #111 devcontainer joins the EPP backend network

Branch `fix/111-devcontainer-epp-network` from `main` (e6fa249). The local changes to `.vscode/settings.json`,
`deploy/ansible/ansible.cfg` and the untracked `config.rri-mtest.yaml.local`, `demo`, `.demo` are carried, never committed.

## Findings

- F1 `docker network connect` exits non-zero when the container is on the network already (a restart keeps it) or the network
  does not exist (backend not up); in `postStartCommand` that fails the start command. With `|| true` both exit 0 (checked
  in the devcontainer: "endpoint ... already exists", "network no_such_net not found").

## Decisions (maintainer, 2026-11-19)

- D1 `postStartCommand` joins `epptest_epp_net`, its failure ignored (`|| true`); docs updated, in a PR of its own.

## Tasks

- [x] T1 `.devcontainer/devcontainer.json`: `... && (docker network connect epptest_epp_net $(cat /etc/hostname) || true)`
- [x] T2 Docs: `docs/agents/testing.project.md`, `README.md` (joined on start; by hand when the backend was not up)
- [x] T3 Checks: lint-imports 28 kept, 0 broken; unit 2869 passed; smoke 190 passed, 440 skipped
