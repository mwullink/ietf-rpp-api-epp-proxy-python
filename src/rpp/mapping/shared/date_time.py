import re

# RFC 3339 §5.6 date-time. The schema checks the `format` too (#233); this check also refuses leap seconds (:60),
# and gives the value with `T` and `Z` in upper case.
_DATE_TIME = re.compile(
    r"[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])[Tt]([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(\.[0-9]+)?([Zz]|[+-]([01][0-9]|2[0-3]):[0-5][0-9])"
)


def rfc3339(timestamp: str) -> str:
    """The date-time with `T` and `Z` in upper case. Anything but an RFC 3339 date-time is a ValueError."""
    if not _DATE_TIME.fullmatch(timestamp):
        raise ValueError(f"'{timestamp}' is not an RFC 3339 date-time")
    return timestamp.upper()
