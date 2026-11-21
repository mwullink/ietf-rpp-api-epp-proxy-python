from dataclasses import dataclass, field

from settings.discovery_settings import DiscoverySettings
from settings.epp_settings import EppSettings
from settings.openapi_settings import OpenApiSettings
from settings.rri_settings import RriSettings
from settings.sqlite_settings import SqliteSettings

BACKENDS = ("epp", "rri", "sqlite")
SIGNALLING_METHODS = ("header", "media-type")


@dataclass(frozen=True)
class Settings:
    """The configuration, by the part of the proxy it is for. `main` loads it once and passes each section on.

    `backend` is the protocol the proxy speaks to the registry (`rpp_backend`): `epp`, `rri`, or `sqlite`, the demo
    backend over a database. `extensions` are the module paths of the extension packages the app is built with
    (`rpp_extensions`): each registers its part of the pipeline. `profile_layers`
    are the layers of its `BackendProfile`, the generic one of the protocol first, then the server's own
    (`rpp_backend_profile`); main merges them with `lgrs`. `preset_signalling` is how a client names the preset of a
    request (`rpp_preset_signalling`, core §Preset Signalling): `header` (the default), or `media-type`. `openapi` is what the
    OpenAPI document served leaves out (`rpp_openapi_omit_*`), nothing by default.
    """
    epp: EppSettings
    discovery: DiscoverySettings
    rri: RriSettings = field(default_factory=RriSettings)
    sqlite: SqliteSettings = field(default_factory=SqliteSettings)
    extensions: tuple[str, ...] = ()
    backend: str = "epp"
    profile_layers: tuple[dict, ...] = ()
    preset_signalling: str = "header"
    openapi: OpenApiSettings = field(default_factory=OpenApiSettings)
    # What the registry does where its protocol leaves the choice to the server (`rpp_protocol_config`): authInfo
    # rules, contact limits, transition periods. The proxy does not use it; the integration suite selects its cases
    # and times its waits by it (docs/agents/testing.project.md#selectors).
    protocol_config: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.backend not in BACKENDS:
            raise ValueError(f"rpp_backend must be one of {', '.join(BACKENDS)}, not {self.backend!r}")
        if self.preset_signalling not in SIGNALLING_METHODS:
            raise ValueError(
                f"rpp_preset_signalling must be one of {', '.join(SIGNALLING_METHODS)}, not "
                f"{self.preset_signalling!r}")

    @property
    def lgrs(self) -> tuple[str, ...]:
        """The LGRs the backend offers for IDNs: those of the EPP IDN tables, or the one of DENIC's repertoire."""
        if self.backend == "sqlite":
            return ()
        if self.backend == "rri":
            return (self.rri.rpp_rri_lgr,) if self.rri.rpp_rri_lgr else ()
        return tuple(sorted(self.epp.rpp_idn_lgr_tables or {}))
