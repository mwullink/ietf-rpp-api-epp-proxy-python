"""The file lock of the mutex and the run setup that runs once per run, across processes (#218)."""
import multiprocessing
import time

from tests.helper.run_directory import run_once
from tests.helper.run_lock import FileLock


def _hold(path, log, seconds):
    with FileLock(path):
        log.put(("in", time.monotonic()))
        time.sleep(seconds)
        log.put(("out", time.monotonic()))


def test_two_processes_never_hold_the_same_lock_at_once(tmp_path):
    log = multiprocessing.Queue()
    processes = [multiprocessing.Process(target=_hold, args=(tmp_path / "q.lock", log, 0.3)) for _ in range(2)]
    for p in processes:
        p.start()
    for p in processes:
        p.join(10)
    events = sorted((log.get(timeout=1) for _ in range(4)), key=lambda e: e[1])

    assert [kind for kind, _ in events] == ["in", "out", "in", "out"]


def _once(directory, log):
    log.put(run_once(directory, "env.run-setup", lambda: (log.put("ran"), time.sleep(0.2))))


def test_the_run_setup_runs_once_however_many_processes_ask(tmp_path):
    log = multiprocessing.Queue()
    processes = [multiprocessing.Process(target=_once, args=(tmp_path, log)) for _ in range(3)]
    for p in processes:
        p.start()
    for p in processes:
        p.join(10)
    events = [log.get(timeout=1) for _ in range(4)]

    assert events.count("ran") == 1 and events.count(None) == 3


def test_a_failed_run_setup_is_reported_to_every_later_asker(tmp_path):
    def fail():
        raise AssertionError("drain failed")

    assert run_once(tmp_path, "env.run-setup", fail) == "drain failed"
    assert run_once(tmp_path, "env.run-setup", lambda: None) == "drain failed"
