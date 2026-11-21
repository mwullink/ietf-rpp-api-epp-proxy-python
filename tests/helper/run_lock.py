"""A lock that processes of one machine share through a file: the mutex of the cases (`exclusive`) and the run
setup, across the xdist workers of a run."""
import fcntl
from pathlib import Path


class FileLock:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._file = None

    def acquire(self) -> None:
        """Waits until no other process holds the lock, without limit."""
        self._file = open(self.path, "a")
        fcntl.flock(self._file, fcntl.LOCK_EX)

    def release(self) -> None:
        if self._file is not None:
            fcntl.flock(self._file, fcntl.LOCK_UN)
            self._file.close()
            self._file = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *_):
        self.release()
