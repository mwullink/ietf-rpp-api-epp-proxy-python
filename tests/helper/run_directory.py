"""The directory of one test run, which its xdist workers share: the locks of the mutex and what the run setup left.

The process that starts the run makes it and names it in `RPP_TEST_RUN_DIR`, which the workers inherit
(tests/integration/conftest.py), and removes it at the end.
"""
import os
import tempfile
from pathlib import Path

from tests.helper.run_lock import FileLock

RUN_DIR_VARIABLE = "RPP_TEST_RUN_DIR"
DONE = ".done"


def new_run_directory() -> Path:
    path = Path(tempfile.mkdtemp(prefix="rpp-test-run-"))
    os.environ[RUN_DIR_VARIABLE] = str(path)
    return path


def run_directory() -> Path:
    """The directory of this run; a process that runs cases without one (a unit test) gets one of its own."""
    value = os.environ.get(RUN_DIR_VARIABLE)
    return Path(value) if value else new_run_directory()


def run_once(directory: Path, key: str, action) -> str | None:
    """Runs `action` once per run and key, whichever process asks first; the others wait for it. None when it
    passed, else its failure, for every process that asks."""
    with FileLock(directory / f"{key}.lock"):
        done = directory / f"{key}{DONE}"
        if not done.exists():
            try:
                action()
                done.write_text("")
            except (Exception, AssertionError) as failure:  # noqa: BLE001 - recorded for every asker
                done.write_text(str(failure) or type(failure).__name__)
        return done.read_text() or None


def keys_done(directory: Path) -> list[str]:
    """The keys whose action ran in this run, passed or failed."""
    return sorted(p.name[:-len(DONE)] for p in directory.glob(f"*{DONE}"))
