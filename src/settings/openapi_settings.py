from dataclasses import dataclass, fields


@dataclass(frozen=True)
class OpenApiSettings:
    """What the OpenAPI document served leaves out (#204). The drafts' API contract lists every operation, also those a server
    does not implement, so both are off by default: switching one on is a deviation from the contract, for a deployment such
    as the demo that shows only what it serves. Routing is the same either way (those requests answer 501). The names are the
    keys of the configuration (config/README.md).

    `rpp_openapi_omit_unheld_objects`: the operations on a data object the backend does not hold under the default preset
    (501 `02307`). `rpp_openapi_omit_unimplemented`: the operations no handler serves (501 `02101`)."""
    rpp_openapi_omit_unheld_objects: bool = False
    rpp_openapi_omit_unimplemented: bool = False

    def __post_init__(self):
        for item in fields(self):
            if not isinstance(getattr(self, item.name), bool):
                raise ValueError(f"{item.name} must be true or false, not {getattr(self, item.name)!r}")
