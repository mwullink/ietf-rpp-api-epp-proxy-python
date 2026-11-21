"""Where the integration case files are: `tests/integration/test_case_data`, or the directory `RPP_TEST_CASE_DATA`
names, which the tests of the runner itself use (tests/unit/test_case_phases.py)."""
import os
from pathlib import Path

CASE_DATA_VARIABLE = "RPP_TEST_CASE_DATA"
DEFAULT = Path(__file__).resolve().parents[1] / "integration" / "test_case_data"


def case_data_dir(environ=None) -> Path:
    environ = os.environ if environ is None else environ
    value = environ.get(CASE_DATA_VARIABLE)
    return Path(value) if value else DEFAULT
