# Process: project specifics

Generic rules are in [process.md](process.md).

Ambiguity in an EPP/RPP mapping counts as "in doubt": ask, because a wrong
assumption in a protocol bridge is expensive to unwind.

## Environment

The system `python --version` is 3.9, but the code uses 3.10+ syntax (`str | None`,
`tuple[...]`, `dict[str,str]`). Use the `.venv` interpreter, which is newer.

## Commands

```bash
# Setup
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt     # requirements.txt plus the development tools

# Run the server (without RPP_CONFIG_FILE: config/environments/epp-docker.yaml)
cd src && uvicorn main:app        # API documentation (Scalar) at http://127.0.0.1:8000/ui/

# Docker
docker build . -f ./.docker/Dockerfile -t pawelk/rpp_server_epp_proxy
docker run --rm -p 8000:8091 pawelk/rpp_server_epp_proxy
```

The deployment image and the Ansible roles are in `deploy/` ([deploy/README.md](../../deploy/README.md)). A change
there is checked with `ansible-lint` and `ansible-playbook --syntax-check site.yml` in `deploy/ansible`, and with the
image built (`docker build -f deploy/docker/Dockerfile .`).

## Configurations

The configurations a change of a key `rpp_*` (or of its values) updates ([process.md](process.md#general-rules), rule
5): the layers of the repository's `config/` tree ([config/README.md](../../config/README.md)), each key in the
layer it belongs to (protocol, backend or environment), and the templates of the example inventory,
`deploy/ansible/inventory/example/configs/*.yaml.j2`. Each template is one flat file made from the repository
environment its header names (`config/environments/<name>.yaml`, with its includes) and takes its keys and values,
except the instance's own (`{{ instance.* }}`, the vault's). The keys the proxy does not know are ignored, with a
warning for an `rpp_*` one: `tests/unit/test_deploy_config_templates.py` renders each template and checks it states no
key its resolved repository environment lacks, the same signalling and profile, and that the proxy starts with it. A change of keys also tells the maintainer to update the inventories outside git
(`deploy/ansible/inventory/<name>/`, and any other copy of the templates).

## Checks before done

CI runs two workflows on every PR, every push to `main` and weekly (Monday 05:00 UTC): `.github/workflows/ci.yml`
(steps 1 and 2, and a Trivy scan of the dependencies, Dockerfiles and secrets) and the supported Python versions (step 5).
Neither reaches a live backend, so run these checks locally from the repository root, in this order:

1. `PYTHONPATH=src lint-imports`: the module boundaries, see
   [architecture.project.md](architecture.project.md#the-check).
2. The unit tests, `pytest -n 4 tests/unit`.
3. The smoke suite, `pytest -n 4 -m smoke tests/integration` (about 2.5 minutes), which needs the live backends: it
   tests every environment whose credentials are in `.env`. See
   [testing.project.md](testing.project.md#test-data-format). The full run, `pytest -n 4` (about 40 minutes), only
   when the maintainer asks for it.
4. For a change to `registry_adapter/rri/`, `core` or `rpp`: the smoke run includes DENIC MTEST before the PR leaves
   draft. Always check first, with one case, whether you (or the agent) can reach MTEST from where the checks run:
   ```bash
   RPP_TEST_ENV=rri-mtest pytest "tests/integration/file_cases.py::rri-mtest::domain_availability::test3-a_label"
   ```
   It logs in and sends one RRI CHECK, and creates nothing. If it passes, the smoke run of step 3 covers MTEST (its
   credentials are in `.env`): record in the plan that it ran. Only if it does not pass, because MTEST cannot be
   reached (no `TEST_RRI_*` in `.env`, a machine not on the allowlist of both RegAccs, a refused login), run
   `RPP_TEST_ENV=epp-docker pytest -n 8 -m smoke tests/integration`, record the MTEST run as pending in the plan with
   the reason, and hand it over to the maintainer.
5. For a change to `requirements*.txt`, or to a test marked `pyversions`: `./test_python_versions.sh` (Docker), which
   the workflow `.github/workflows/python-versions.yml` also runs on every PR. See
   [testing.project.md](testing.project.md#supported-python-versions).

## Issue labels

Use `bug` for defects, plus one `severity:*` label (`critical`, `high`, `medium`,
`low`) and one `area:*` label (`functional`, `spec-compliance`, `not-implemented`,
`tech-debt`, `refactoring`, `performance`, `build`, `chores`).

## Dependency updates

Renovate ([renovate.json](../../renovate.json)) opens its PRs on Monday mornings, for no release younger than 24 hours
(`minimumReleaseAge`): one PR for the minor and patch updates of `requirements*.txt`, one for the GitHub Actions and
images, and one per major update. The non-major PRs merge themselves once CI passes; a major one is merged by hand. The
Python images stay on 3.11 (`allowedVersions`). A Trivy finding of HIGH or CRITICAL with a fix fails CI: update the pin,
or wait for Renovate's PR.
