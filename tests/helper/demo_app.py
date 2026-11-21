"""An app of the SQLite demo backend (config/environments/sqlite-demo.yaml) with the demo extensions and the offers a test composes (the demo
configurations of #180, config.demo-*.yaml, are composed from their files, see tests/unit/test_demo_configurations.py): which extensions the configuration names, which presets it offers, and the profiles it binds."""
import dataclasses

from main import compose
from settings.load_settings import load_settings
from settings.sqlite_settings import SqliteSettings
from tests.helper.test_environment import REPOSITORY

PLANETS = "extensions.planets"
ATMOSPHERE = "extensions.planet_atmosphere"
ORBIT = "extensions.satellite_orbit"

ALL_EXTENSIONS = (PLANETS, ATMOSPHERE, ORBIT)
ALL_PRESETS = ("planets", "planets-atmosphere", "planets-orbits", "planets-complete", "catalogued-planets", "habitable-worlds")


def demo_composition(database, extensions=ALL_EXTENSIONS, presets=ALL_PRESETS, bound=None, signalling="header"):
    """The composition of an app over the database file, offering `presets` (the first is the default)."""
    settings = load_settings(str(REPOSITORY / "config/environments/sqlite-demo.yaml"))
    specific = {**settings.profile_layers[1], "presets": list(presets), "default_preset": presets[0],
                "bound_profiles": bound or {}}
    return compose(dataclasses.replace(
        settings, extensions=tuple(extensions), preset_signalling=signalling,
        profile_layers=(settings.profile_layers[0], specific, *settings.profile_layers[2:]),
        sqlite=SqliteSettings(rpp_sqlite_url=f"sqlite:///{database}", rpp_sqlite_clients=settings.sqlite.rpp_sqlite_clients)))
