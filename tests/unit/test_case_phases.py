"""The phases of an integration case as pytest reports them (#218): an inner pytest runs case files of a temporary
case directory (`RPP_TEST_CASE_DATA`) against `sqlite-demo`, which needs no server and no credentials."""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parents[2]
HEADERS = {"Authorization": "{auth:a}", "Accept": "{rpp:accept}", "RPP-Preset": "{rpp:preset}",
           "Content-Type": "{rpp:content-type}", "RPP-Cltrid": "{unique_cltrid}"}


def request(method, url, body=None):
    request = {"method": method, "url": url, "headers": HEADERS}
    if body is not None:
        request["body_json"] = body
    return request


def create(suffix):
    return {"comment": "Creates a planet.", "request": request("POST", "/planets", {
        "@type": "planet", "id": f"{{handle:a:{suffix}}}", "type": "rocky", "radius": 1.0,
        "authInfo": {"@type": "authInfo", "method": "authinfo", "authdata": "Secret-Word1"}}),
        "response": {"status": 201, "body": {"@type": "planet"}}, "capture": {"planet": "id"}}


def read(status=200):
    return {"comment": "Reads the planet.", "request": request("GET", "/planets/{capture:planet}"),
            "response": {"status": status, "body": {}}}


def delete(url="/planets/{capture:planet}"):
    return {"comment": "Deletes a planet.", "request": request("DELETE", url), "response": {"status": 200}}


FAILING_TEARDOWN = delete("/planets/{handle:a:-nope}")  # no such planet: 404, a warning


def run_inner(tmp_path, cases, run_hooks=None, includes=None):
    data = tmp_path / "case_data"
    (data / "g").mkdir(parents=True)
    (data / "g" / "_group.json").write_text(json.dumps({"when": {"profile.objects": {"contains": "planet"}}}))
    for name, case in cases.items():
        (data / "g" / f"{name}.json").write_text(json.dumps(case))
    (data / "_includes").mkdir()
    for name, include in (includes or {}).items():
        (data / "_includes" / f"{name}.json").write_text(json.dumps(include))
    if run_hooks is not None:
        (data / "_run.json").write_text(json.dumps(run_hooks))
    junit = tmp_path / "junit.xml"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTEST_", "RPP_TEST_RUN_DIR"))}
    env.update(RPP_TEST_ENV="sqlite-demo", RPP_TEST_CASE_DATA=str(data))
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/integration/file_cases.py", "-p", "no:cacheprovider",
                             "-k", "sqlite-demo and not sqlite-demo-", f"--junitxml={junit}", "-rA"],
                            cwd=REPOSITORY, env=env, capture_output=True, text=True, timeout=600)
    outcomes = {}
    for case in ElementTree.parse(junit).getroot().iter("testcase"):
        kinds = [child.tag for child in case if child.tag in ("failure", "error", "skipped")]
        messages = " ".join(child.get("message", "") + (child.text or "") for child in case)
        outcomes[case.get("name")] = (kinds[0] if kinds else "passed", messages)
    return outcomes, warnings_section(result.stdout)


def warnings_section(stdout: str) -> str:
    """The lines of the `teardown warnings` section of the summary, empty without one."""
    lines = stdout.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("=") and " teardown warnings " in line]
    if not starts:
        return ""
    section = []
    for line in lines[starts[0] + 1:]:
        if line.startswith("="):
            break
        section.append(line)
    return "\n".join(section)


@pytest.fixture(scope="module")
def phases(tmp_path_factory):
    return run_inner(tmp_path_factory.mktemp("phases"), {
        "passes": {"setup": [create("-p1")], "steps": [read()], "teardown": [FAILING_TEARDOWN, delete()]},
        "setup_fails": {"setup": [read()], "steps": [read()], "teardown": [FAILING_TEARDOWN]},
        "test_fails": {"setup": [create("-p2")], "steps": [read(status=410)], "teardown": [delete(), FAILING_TEARDOWN]},
        "uses_include": {"setup": [{"comment": "c", "include": "make", "with": {"suffix": "-p3"}}],
                         "steps": [{"comment": "c", "loop": [{**read(), "until": {"status": 200}}]}],
                         "teardown": [delete()]},
        "unknown_include": {"steps": [{"comment": "c", "include": "nope"}]},
    }, includes={"make": {"comment": "c", "parameters": {"suffix": {"comment": "c"}}, "steps": [create("{param:suffix}")]}})


def test_a_case_whose_teardown_fails_passes_with_a_warning_naming_the_step(phases):
    outcomes, stdout = phases

    assert outcomes["passes"][0] == "passed"
    assert "passes teardown[0]: " in stdout and "passes teardown[1]" not in stdout


def test_a_failing_setup_is_an_error_and_the_teardown_still_runs(phases):
    outcomes, stdout = phases

    assert outcomes["setup_fails"][0] == "error"
    assert "setup_fails setup[0]: " in outcomes["setup_fails"][1]
    assert "setup_fails teardown[0]: " in stdout


def test_a_failing_step_is_a_failure_and_the_teardown_still_runs(phases):
    outcomes, stdout = phases

    assert outcomes["test_fails"][0] == "failure"
    assert "test_fails steps[0]: " in outcomes["test_fails"][1]
    assert "test_fails teardown[1]: " in stdout and "test_fails teardown[0]" not in stdout


def test_an_include_with_a_parameter_and_its_capture_serve_the_case(phases):
    assert phases[0]["uses_include"][0] == "passed"


def test_an_unknown_include_fails_the_case_at_load_naming_it(phases):
    outcome, message = phases[0]["unknown_include"]

    assert outcome == "failure" and "unknown include 'nope'" in message


def test_a_failing_run_setup_is_an_error_of_every_case_and_its_teardown_runs(tmp_path):
    outcomes, stdout = run_inner(tmp_path, {"a": {"steps": []}, "b": {"steps": []}}, run_hooks={
        "setup": [{**FAILING_TEARDOWN, "comment": "Fails."}], "teardown": [FAILING_TEARDOWN]})

    assert {name: outcome for name, (outcome, _) in outcomes.items()} == {"a": "error", "b": "error"}
    assert "run setup of sqlite-demo failed" in outcomes["a"][1]
    assert "run teardown[0]: " in stdout
