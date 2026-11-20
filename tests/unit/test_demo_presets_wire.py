"""The demo presets and profiles as the proxy publishes them (#179): the union of the bases once, the Preset Schema of a preset with
the extensions and the profiles that apply, discovery, and an app whose configuration lacks an extension that only some presets need."""
import base64

import pytest
from starlette.testclient import TestClient

from registration import load_extensions
from rpp.schema.definitions import Definitions
from rpp.schema.extension_registration import register_all
from rpp.schema.extensions import EXTENSIONS
from rpp.schema.offered_presets import OfferedPresets
from tests.helper.demo_app import ATMOSPHERE, PLANETS, demo_composition
from tests.helper.preset_fixtures import BASE, preset as fixture_preset, registry_with

ATMOSPHERE_ID = "org.example.rpp.extension.planet-atmosphere"
PLANETS_ID = "org.example.rpp.extension.planets"
MEDIA_TYPE = "application/rpp+json"
HEADERS = {"Authorization": "Basic " + base64.b64encode(b"demo-a:demo-a-password").decode(), "Accept": MEDIA_TYPE,
           "RPP-Cltrid": "t-1"}


def preset(key):
    return f"org.example.rpp.preset.{key}"


def profile(key):
    return f"org.example.rpp.profile.{key}"


def extension(key):
    return f"org.example.rpp.extension.{key}"


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    composition = demo_composition(tmp_path_factory.mktemp("demo") / "demo.db", bound={"planets-complete": ["catalogued-satellites"]})
    yield TestClient(composition.app)
    composition.sessions.close()


def read(client, path, **headers):
    return client.get(path, headers={**HEADERS, **headers})


def references(items):
    return [item["id"] for item in items]


def test_a_preset_with_two_bases_is_their_union_and_what_two_bases_share_is_in_it_once(client):
    body = read(client, f"/presets/{preset('planets-complete')}").json()

    assert sorted(references(body["extensions"])) == sorted(
        [extension("planets"), extension("planet-atmosphere"), extension("satellite-orbit")])
    assert references(body["boundProfiles"]) == [profile("catalogued-satellites")]


def test_a_preset_with_profiles_through_its_bases_has_each_profile_once_with_the_bases_first(client):
    body = read(client, f"/presets/{preset('habitable-worlds')}").json()

    assert sorted(references(body["extensions"])) == sorted([extension("planets"), extension("planet-atmosphere")])
    assert sorted(references(body["profiles"])) == sorted(
        [profile("rocky-planets"), profile("catalogued-satellites"), profile("habitable-rocky-planets")])


def test_a_profile_is_read_with_its_url_its_bases_and_the_extensions_it_requires(client):
    body = read(client, f"/profiles/{profile('habitable-rocky-planets')}").json()

    assert body["url"].endswith("/docs/demo/habitable-rocky-planets-profile.md")
    assert references(body["baseProfiles"]) == [profile("rocky-planets"), profile("habitable-atmospheres")]
    # the read definition is flattened: what the profile requires through its bases too
    assert sorted(references(body["requiredExtensions"])) == sorted([extension("planets"), extension("planet-atmosphere")])


def test_the_schema_of_a_preset_has_its_extensions_and_the_constraints_of_every_profile_that_applies(client):
    schema = read(client, f"/presets/{preset('habitable-worlds')}/schema", Accept="application/schema+json").json()

    defs = schema["$defs"]
    assert "profile.rocky.type" in defs and "profile.habitable.pressure" in defs and "profile.habitableRocky.radius" in defs
    assert "ext.orbit.satellite.create" not in defs     # the extension is not in the preset
    assert "atmosphere" in defs and "orbit" not in defs
    assert [item["$ref"] for item in defs["planet.create"]["allOf"][1:]][:1] == ["#/$defs/ext.atmosphere.planet.create"]


def test_discovery_lists_every_offered_preset_and_each_extension_once(client):
    body = read(client, "/.well-known/rpp").json()

    assert [item["id"] for item in body["presets"]] == [preset(key) for key in (
        "planets", "planets-atmosphere", "planets-orbits", "planets-complete", "catalogued-planets", "habitable-worlds")]
    assert [item["id"] for item in body["extensions"]] == [extension("planets"), extension("planet-atmosphere"),
                                                           extension("satellite-orbit")]


def test_an_app_without_the_orbit_extension_starts_and_does_not_know_the_presets_that_need_it(tmp_path):
    presets = ("planets", "planets-atmosphere", "catalogued-planets", "habitable-worlds")
    composition = demo_composition(tmp_path / "demo.db", extensions=(PLANETS, ATMOSPHERE), presets=presets)
    try:
        client = TestClient(composition.app)

        assert read(client, f"/presets/{preset('habitable-worlds')}").status_code == 200
        assert read(client, f"/presets/{preset('planets-orbits')}").status_code == 404
        assert read(client, f"/presets/{preset('planets-complete')}").status_code == 404
    finally:
        composition.sessions.close()


def test_a_configuration_that_offers_a_preset_of_an_extension_it_does_not_name_does_not_start(tmp_path):
    with pytest.raises(ValueError, match="unknown preset planets-orbits"):
        demo_composition(tmp_path / "demo.db", extensions=(PLANETS, ATMOSPHERE), presets=("planets", "planets-orbits"))


def test_a_preset_that_has_the_atmosphere_extension_without_the_planets_extension_does_not_start():
    registry = load_extensions([PLANETS, ATMOSPHERE])
    register_all(registry)
    atmosphere_only = fixture_preset("atmosphere-only", base_presets=[BASE["id"]], extensions=[(ATMOSPHERE_ID, "1.0")])
    definitions = Definitions.load(registry, EXTENSIONS)
    definitions.presets["atmosphere-only"] = Definitions.load(registry_with([atmosphere_only]), EXTENSIONS).presets["atmosphere-only"]

    with pytest.raises(ValueError, match=f"{ATMOSPHERE_ID} extends planet.create of the extension {PLANETS_ID}.*atmosphere-only"):
        OfferedPresets.build(definitions, ["atmosphere-only"], "atmosphere-only", {}, (ATMOSPHERE_ID, PLANETS_ID))
