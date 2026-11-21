import logging
import os
from dataclasses import fields
from pathlib import Path

import yaml

from settings.discovery_settings import DiscoverySettings
from settings.epp_settings import EppSettings
from settings.layered_yaml import load_layered
from settings.openapi_settings import OpenApiSettings
from settings.rri_settings import RriSettings
from settings.sqlite_settings import SqliteSettings
from settings.settings import BACKENDS, Settings

logger = logging.getLogger(__name__)

# The generic profile of each protocol, which the profile of a server extends.
PROFILES = Path(__file__).resolve().parent / "profiles"
# The configuration without RPP_CONFIG_FILE: the EPP test server of the repository's config/ tree. In the development
# image src/ is /app, so this is /config/environments/epp-docker.yaml there.
DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "environments" / "epp-docker.yaml"
SECTIONS = (EppSettings, DiscoverySettings, RriSettings, SqliteSettings, OpenApiSettings)
# The keys load_settings reads besides the fields of the sections.
TOP_LEVEL_KEYS = ("rpp_backend", "rpp_backend_profile", "rpp_extensions", "rpp_preset_signalling", "rpp_protocol_config")
KNOWN_KEYS = frozenset(TOP_LEVEL_KEYS) | {f.name for section in SECTIONS for f in fields(section)}


def _section(section, data: dict):
    return section(**{f.name: data[f.name] for f in fields(section) if f.name in data})


def _profile_layers(data: dict, backend: str) -> tuple[dict, ...]:
    """The layers of the backend profile: the generic profile `extends` names (the protocol's by default), then
    what `rpp_backend_profile` states besides."""
    specific = dict(data.get("rpp_backend_profile") or {})
    generic = specific.pop("extends", backend)
    if generic not in BACKENDS:
        raise ValueError(f"rpp_backend_profile extends one of {', '.join(BACKENDS)}, not {generic!r}")
    with open(PROFILES / f"{generic}.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f), specific


def _extensions(data: dict) -> tuple[str, ...]:
    """The module paths of `rpp_extensions`: a list of strings, none twice."""
    paths = data.get("rpp_extensions") or []
    if not isinstance(paths, list) or not all(isinstance(path, str) and path for path in paths):
        raise ValueError("rpp_extensions must be a list of module paths")
    if len(set(paths)) != len(paths):
        raise ValueError("rpp_extensions names a module twice")
    return tuple(paths)


def load_settings(config_path: str | None = None) -> Settings:
    """Reads `config_path`, else the file `RPP_CONFIG_FILE` names, else `DEFAULT_CONFIG`, with its includes and the
    untracked `<name>.local.yaml` of every layer (settings/layered_yaml.py). A top-level key whose value is null is
    absent, so a local file unsets a key with null. A key the proxy does not know is ignored, with a warning for one
    that looks like the proxy's (`rpp_*`)."""
    config_path = config_path or os.getenv("RPP_CONFIG_FILE") or str(DEFAULT_CONFIG)
    layered = load_layered(config_path)
    data = {key: value for key, value in layered.data.items() if value is not None}
    for key in sorted(data):
        if key.startswith("rpp_") and key not in KNOWN_KEYS:
            logger.warning("Unknown configuration key %s in %s: ignored", key, layered.sources[key])
    backend = data.get("rpp_backend", "epp")
    return Settings(
        epp=_section(EppSettings, data), discovery=_section(DiscoverySettings, data), rri=_section(RriSettings, data),
        sqlite=_section(SqliteSettings, data), extensions=_extensions(data), backend=backend, profile_layers=_profile_layers(data, backend) if backend in BACKENDS else (),
        preset_signalling=data.get("rpp_preset_signalling", "header"), openapi=_section(OpenApiSettings, data),
        protocol_config=_protocol_config(data),
    )


def _protocol_config(data: dict) -> dict:
    """`rpp_protocol_config`: a mapping, which the proxy keeps but does not use."""
    value = data.get("rpp_protocol_config") or {}
    if not isinstance(value, dict):
        raise ValueError("rpp_protocol_config must be a mapping")
    return value
