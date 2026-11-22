"""One case in one environment, phase by phase, as the pytest item of `conftest.py` runs it (#218)."""
import datetime

import pytest
from starlette.testclient import TestClient

from tests.helper.run_directory import run_directory
from tests.helper.run_lock import FileLock
from tests.helper.step_runner import StepRunner
from tests.integration.file_cases import EnvironmentRun, preparer


class CaseRun:
    """One case in one environment, phase by phase, as the pytest item runs it: `setup` takes the mutexes (`exclusive`)
    and runs the run setup if no case has yet, then the case's `setup`; `test` runs `steps`; `teardown` runs the
    case's `teardown` whatever happened before, and returns what failed in it."""

    def __init__(self, case, run: EnvironmentRun):
        self.case = case
        self.run = run
        self.locks = []
        self.client = None
        self.runner = None

    def setup(self) -> None:
        if "skip" in self.case:
            pytest.skip(reason=f"Skipping test case: {self.case['test_id']} - {self.case['skip']}")
        self.run.ensure_run_setup()
        for name in sorted(set(self.case.get("exclusive", []))):
            lock = FileLock(run_directory() / f"{self.run.server}.{name}.lock")     # the mutex is the server's
            lock.acquire()
            self.locks.append(lock)
        self.client = TestClient(self.run.app)
        self.client.__enter__()
        # {test_start} is the start of this case, so the time windows in the data do not depend on suite length.
        self.runner = StepRunner(self.client, preparer(self.case, self.run, datetime.datetime.now(datetime.UTC)),
                                 self.case["test_id"], self.run.environment.preset_signalling, self.run.credentials,
                                 self.run.pacer)
        self.runner.run(self.case.get("setup", []), "setup")

    def test(self) -> None:
        self.runner.run(self.case["steps"], "steps")

    def teardown(self) -> list[str]:
        try:
            return self.runner.run_teardown(self.case.get("teardown", [])) if self.runner is not None else []
        finally:
            if self.client is not None:
                self.client.__exit__(None, None, None)
            for lock in reversed(self.locks):
                lock.release()
