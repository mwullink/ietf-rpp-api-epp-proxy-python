"""The demo configurations of #180 (config/environments/sqlite-demo.yaml, the bare one, and sqlite-demo-extended, -bound and -inherit),
composed from the files as they are: what each publishes (discovery, the Preset and Profile Data Objects, the Preset Schema) with
the bound profiles apart and the bases flattened once, and what each accepts and refuses. The integration environments of the
same names (tests/integration/environments/) run the cases of the plain objects and of the binding against the same files."""
import base64
import dataclasses
import json

import pytest
from starlette.testclient import TestClient

from main import compose
from settings.load_settings import load_settings
from settings.sqlite_settings import SqliteSettings
from tests.helper.test_environment import REPOSITORY

MEDIA_TYPE = "application/rpp+json"
BASIC = "Basic " + base64.b64encode(b"demo-a:demo-a-password").decode()
SECRET = "Secret-Word1"


def p(key):
    return f"org.example.rpp.preset.{key}"


def q(key):
    return f"org.example.rpp.profile.{key}"


def e(key):
    return f"org.example.rpp.extension.{key}"


PLANETS, ATMOSPHERE, ORBIT = e("planets"), e("planet-atmosphere"), e("satellite-orbit")

CONFIGS = {
    "bare": "config/environments/sqlite-demo.yaml", "extended": "config/environments/sqlite-demo-extended.yaml",
    "bound": "config/environments/sqlite-demo-bound.yaml",
    "inherit": "config/environments/sqlite-demo-inherit.yaml",
}


class Server:
    """An app composed from a configuration file, with a database file of its own."""

    def __init__(self, name, directory):
        settings = load_settings(str(REPOSITORY / CONFIGS[name]))
        self.settings = dataclasses.replace(settings, sqlite=SqliteSettings(
            rpp_sqlite_url=f"sqlite:///{directory / (name + '.db')}", rpp_sqlite_clients=settings.sqlite.rpp_sqlite_clients))
        self.composition = compose(self.settings)
        self.client = TestClient(self.composition.app)
        self.signalling = self.settings.preset_signalling
        self.default = p(self.settings.profile_layers[1]["default_preset"])
        self.counter = 0

    def headers(self, preset=None, accept=None):
        preset = p(preset) if preset else self.default
        self.counter += 1
        headers = {"Authorization": BASIC, "RPP-Cltrid": f"t-{self.counter}"}
        if self.signalling == "header":
            headers.update({"Accept": accept or MEDIA_TYPE, "Content-Type": MEDIA_TYPE,
                            "RPP-Preset": f"preset={preset};version=1.0"})
        else:
            typed = f'{MEDIA_TYPE}; preset="{preset}"; preset-version="1.0"'
            headers.update({"Accept": accept or typed, "Content-Type": typed})
        return headers

    def get(self, path, preset=None, accept=None):
        return self.client.get(path, headers=self.headers(preset, accept))

    def read(self, path, preset=None, accept=None):
        response = self.get(path, preset, accept)
        assert response.status_code == 200, response.text
        return response.json()

    def schema(self, key):
        return self.client.get(f"/presets/{p(key)}/schema", headers={"Accept": "application/schema+json"}).json()

    def post(self, url, body, preset=None):
        return self.client.request("POST", url, headers=self.headers(preset), content=json.dumps(body))


@pytest.fixture(scope="module")
def servers(tmp_path_factory):
    directory = tmp_path_factory.mktemp("configurations")
    built = {name: Server(name, directory) for name in CONFIGS}
    yield built
    for server in built.values():
        server.composition.sessions.close()


def ids(items):
    """The identifiers of a list, sorted: the order is not specified. A duplicate fails the test, as each item is there once."""
    found = [item["id"] for item in items]
    assert len(found) == len(set(found)), f"an item twice: {found}"
    return sorted(found)


def planet(name, **members):
    body = {"@type": "planet", "id": name, "type": "rocky", "radius": 3389.5,
            "authInfo": {"@type": "authInfo", "method": "authinfo", "authdata": SECRET}, **members}
    return {key: value for key, value in body.items() if value is not None}


def refusal(response, profile):
    assert response.status_code == 422, response.text
    error = response.json()["errors"][0]
    assert response.headers["RPP-Code"] == "02308" and error["result"] == "02308" and error["profile"] == q(profile)


# --- discovery: the offered presets and each extension once

OFFERED = {
    "bare": ("base", "planets"),
    "extended": ("base", "planets", "planets-atmosphere", "planets-orbits", "planets-complete"),
    "bound": ("base", "planets", "planets-atmosphere", "planets-complete", "catalogued-planets"),
    "inherit": ("base", "planets", "planets-atmosphere", "planets-orbits", "planets-complete", "catalogued-planets",
                "habitable-worlds"),
}
EXTENSIONS = {"bare": [PLANETS], "extended": [PLANETS, ATMOSPHERE, ORBIT], "bound": [PLANETS, ATMOSPHERE, ORBIT],
              "inherit": [PLANETS, ATMOSPHERE, ORBIT]}


@pytest.mark.parametrize("name", CONFIGS)
def test_discovery_lists_the_offered_presets_and_each_extension_once(servers, name):
    body = servers[name].read("/.well-known/rpp")

    assert ids(body["presets"]) == sorted("urn:ietf:params:rpp:preset:base" if key == "base" else p(key) for key in OFFERED[name])
    assert ids(body["extensions"]) == sorted(EXTENSIONS[name])
    assert [item["id"] for item in body["presets"] if item["defaultPreset"]] == [servers[name].default]


def test_discovery_lists_each_profile_that_applies_once_with_the_bases_of_a_bound_one(servers):
    assert ids(servers["bound"].read("/.well-known/rpp")["profiles"]) == sorted([
        q("rocky-planets"), q("catalogued-satellites"), q("habitable-atmospheres"), q("habitable-rocky-planets")])
    assert ids(servers["inherit"].read("/.well-known/rpp")["profiles"]) == sorted([
        q("rocky-planets"), q("catalogued-satellites"), q("habitable-atmospheres"), q("habitable-rocky-planets")])
    assert servers["extended"].read("/.well-known/rpp").get("profiles", []) == []
    assert servers["bare"].read("/.well-known/rpp").get("profiles", []) == []


# --- the Preset Data Object: the extensions of the bases once, the profiles of the definition apart from the bound ones

def test_extended_has_no_profile_and_a_preset_with_two_bases_has_the_union_of_their_extensions_once(servers):
    body = servers["extended"].read(f"/presets/{p('planets-complete')}")

    assert ids(body["extensions"]) == sorted([PLANETS, ATMOSPHERE, ORBIT])
    assert body.get("profiles", []) == [] and body["boundProfiles"] == [] and body["defaultPreset"] is True


def test_bound_shows_the_profiles_of_the_definition_and_the_bound_ones_apart(servers):
    bound = servers["bound"]

    assert ids(bound.read(f"/presets/{p('planets')}")["boundProfiles"]) == [q("rocky-planets")]
    assert bound.read(f"/presets/{p('planets')}").get("profiles", []) == []
    definition = bound.read(f"/presets/{p('catalogued-planets')}")
    assert ids(definition["profiles"]) == sorted([q("rocky-planets"), q("catalogued-satellites")])
    assert definition["boundProfiles"] == []
    complete = bound.read(f"/presets/{p('planets-complete')}")
    assert ids(complete["extensions"]) == sorted([PLANETS, ATMOSPHERE, ORBIT])
    assert complete.get("profiles", []) == [] and ids(complete["boundProfiles"]) == [q("habitable-rocky-planets")]


def test_inherit_flattens_two_bases_and_a_profile_both_a_base_and_the_profile_reach_counts_once(servers):
    inherit = servers["inherit"]
    worlds = inherit.read(f"/presets/{p('habitable-worlds')}")

    assert ids(worlds["extensions"]) == sorted([PLANETS, ATMOSPHERE])
    assert ids(worlds["profiles"]) == sorted([q("rocky-planets"), q("catalogued-satellites"), q("habitable-rocky-planets")])
    assert worlds["boundProfiles"] == []
    assert ids(inherit.read(f"/presets/{p('planets-complete')}")["extensions"]) == sorted([PLANETS, ATMOSPHERE, ORBIT])


@pytest.mark.parametrize("name", ["bound", "inherit"])
def test_a_profile_with_two_bases_is_read_with_its_bases_and_the_extensions_they_require(servers, name):
    body = servers[name].read(f"/profiles/{q('habitable-rocky-planets')}")

    assert ids(body["baseProfiles"]) == sorted([q("rocky-planets"), q("habitable-atmospheres")])
    assert ids(body["requiredExtensions"]) == sorted([PLANETS, ATMOSPHERE])


# --- the Preset Schema: the extensions of the preset and the constraints of every profile that applies

DEMO_PROFILE_DEFS = ("profile.rocky.", "profile.catalogued.", "profile.habitable.", "profile.habitableRocky.")


def profile_defs(schema):
    """The definitions of the demo profiles in a Preset Schema."""
    return sorted(key for key in schema["$defs"] if key.startswith(DEMO_PROFILE_DEFS))


def test_the_schema_of_a_preset_has_the_profile_that_a_server_binds_and_the_one_without_binding_has_none(servers):
    assert "profile.rocky.type" in servers["bound"].schema("planets")["$defs"]
    assert profile_defs(servers["bare"].schema("planets")) == []
    assert profile_defs(servers["extended"].schema("planets-complete")) == []
    assert "ext.atmosphere.planet.create" in servers["extended"].schema("planets-complete")["$defs"]
    assert "ext.atmosphere.planet.create" not in servers["extended"].schema("planets")["$defs"]


def test_the_schema_of_a_bound_profile_with_bases_has_the_constraints_of_its_bases(servers):
    defs = profile_defs(servers["bound"].schema("planets-complete"))

    assert "profile.rocky.type" in defs and "profile.habitable.pressure" in defs and "profile.habitableRocky.radius" in defs


def test_the_profile_a_base_preset_and_a_base_profile_both_reach_is_in_the_schema_once(servers):
    schema = servers["inherit"].schema("habitable-worlds")

    refs = [ref["$ref"] for ref in schema["$defs"]["planet.create"]["allOf"][1:]]
    assert refs.count("#/$defs/profile.rocky.type") == 1
    assert len(refs) == len(set(refs))
    assert "profile.rocky.type" in schema["$defs"] and "ext.orbit.satellite.create" not in schema["$defs"]


# --- the binding: the same request accepted without it, refused with it

def test_a_gas_giant_is_accepted_by_the_preset_without_the_profile_and_refused_where_the_server_binds_it(servers):
    assert servers["bare"].post("/planets", planet("jupiter", type="gas-giant")).status_code == 201
    refusal(servers["bound"].post("/planets", planet("jupiter", type="gas-giant")), "rocky-planets")


def test_a_bound_profile_constrains_the_extension_of_its_preset_and_the_same_planet_is_accepted_without_it(servers):
    without_atmosphere = planet("venus")

    refusal(servers["bound"].post("/planets", without_atmosphere, "planets-atmosphere"), "habitable-atmospheres")
    assert servers["extended"].post("/planets", without_atmosphere, "planets-atmosphere").status_code == 201


def test_a_bound_profile_enforces_the_constraints_of_its_bases(servers):
    bound = servers["bound"]
    atmosphere = {"@type": "atmosphere", "pressure": 1.0}

    refusal(bound.post("/planets", planet("a1"), "planets-complete"), "habitable-atmospheres")
    refusal(bound.post("/planets", planet("a2", radius=None, atmosphere=atmosphere), "planets-complete"),
            "habitable-rocky-planets")
    refusal(bound.post("/planets", planet("a3", type="gas-giant", atmosphere=atmosphere), "planets-complete"),
            "rocky-planets")
    assert bound.post("/planets", planet("a4", atmosphere=atmosphere), "planets-complete").status_code == 201
    extended = servers["extended"]
    assert extended.post("/planets", planet("a5", radius=None, type="gas-giant"), "planets-complete").status_code == 201


def test_a_member_of_an_extension_outside_the_preset_is_400(servers):
    response = servers["extended"].post("/planets", planet("b1", atmosphere={"@type": "atmosphere", "pressure": 1.0}), "planets")

    assert response.status_code == 400
    assert response.headers["RPP-Code"] == "02001"


def test_the_preset_of_the_definition_applies_to_every_server_that_offers_it(servers):
    worlds = servers["inherit"]

    refusal(worlds.post("/planets", planet("c1", type="gas-giant", atmosphere={"@type": "atmosphere", "pressure": 1.0}),
                        "habitable-worlds"), "rocky-planets")


# --- the profiles of each offered preset, exactly: the ones of its definition and the ones the server binds

ROCKY, CATALOGUED, HABITABLE_ATMOSPHERES, HABITABLE_ROCKY = (
    q("rocky-planets"), q("catalogued-satellites"), q("habitable-atmospheres"), q("habitable-rocky-planets"))
BASE = "urn:ietf:params:rpp:preset:base"

# {preset: (profiles of the definition, bound profiles)}
PROFILES_OF_PRESETS = {
    "bare": {BASE: ([], []), p("planets"): ([], [])},
    "extended": {BASE: ([], []), **{p(key): ([], []) for key in OFFERED["extended"][1:]}},
    "bound": {BASE: ([], []), p("planets"): ([], [ROCKY]), p("planets-atmosphere"): ([], [HABITABLE_ATMOSPHERES]),
              p("planets-complete"): ([], [HABITABLE_ROCKY]), p("catalogued-planets"): ([ROCKY, CATALOGUED], [])},
    "inherit": {BASE: ([], []), p("planets"): ([], []), p("planets-atmosphere"): ([], []), p("planets-orbits"): ([], []),
                p("planets-complete"): ([], []), p("catalogued-planets"): ([ROCKY, CATALOGUED], []),
                p("habitable-worlds"): ([ROCKY, CATALOGUED, HABITABLE_ROCKY], [])},
}


@pytest.mark.parametrize("name", CONFIGS)
def test_discovery_shows_for_each_offered_preset_its_profiles_and_the_bound_ones_apart(servers, name):
    shown = {entry["id"]: (ids(entry.get("profiles", [])), ids(entry.get("boundProfiles", [])))
             for entry in servers[name].read("/.well-known/rpp")["presets"]}

    assert shown == {key: (sorted(profiles), sorted(bound)) for key, (profiles, bound) in PROFILES_OF_PRESETS[name].items()}


def test_a_preset_with_a_bound_profile_and_none_in_its_definition_shows_only_the_bound_one(servers):
    body = servers["bound"].read(f"/presets/{p('planets-atmosphere')}")

    assert ids(body["boundProfiles"]) == [HABITABLE_ATMOSPHERES]
    assert body.get("profiles", []) == []


# --- the Preset Schema of each offered preset, exactly: the sub-schemas of its extensions and of the profiles that apply to it

ATMOSPHERE_DEFS = ["ext.atmosphere.planet.create", "ext.atmosphere.planet.read", "ext.atmosphere.planet.update"]
ORBIT_DEFS = ["ext.orbit.satellite.create", "ext.orbit.satellite.read", "ext.orbit.satellite.update"]
HABITABLE_DEFS = ["profile.habitable.atmosphere", "profile.habitable.pressure"]
ROCKY_DEFS = ["profile.rocky.type"]
CATALOGUED_DEFS = ["profile.catalogued.id"]
HABITABLE_ROCKY_DEFS = ["profile.habitableRocky.radius"]

# {preset: (sub-schemas of the extensions, sub-schemas of the profiles)}
SCHEMAS_OF_PRESETS = {
    "bare": {"planets": ([], [])},
    "extended": {"planets": ([], []), "planets-atmosphere": (ATMOSPHERE_DEFS, []), "planets-orbits": (ORBIT_DEFS, []),
                 "planets-complete": (ATMOSPHERE_DEFS + ORBIT_DEFS, [])},
    "bound": {"planets": ([], ROCKY_DEFS), "planets-atmosphere": (ATMOSPHERE_DEFS, HABITABLE_DEFS),
              "planets-complete": (ATMOSPHERE_DEFS + ORBIT_DEFS, HABITABLE_DEFS + HABITABLE_ROCKY_DEFS + ROCKY_DEFS),
              "catalogued-planets": ([], CATALOGUED_DEFS + ROCKY_DEFS)},
    "inherit": {"planets": ([], []), "planets-atmosphere": (ATMOSPHERE_DEFS, []), "planets-orbits": (ORBIT_DEFS, []),
                "planets-complete": (ATMOSPHERE_DEFS + ORBIT_DEFS, []), "catalogued-planets": ([], CATALOGUED_DEFS + ROCKY_DEFS),
                "habitable-worlds": (ATMOSPHERE_DEFS, CATALOGUED_DEFS + HABITABLE_DEFS + HABITABLE_ROCKY_DEFS + ROCKY_DEFS)},
}


@pytest.mark.parametrize("name", CONFIGS)
def test_the_schema_of_each_offered_preset_has_the_sub_schemas_of_its_own_extensions_and_profiles_only(servers, name):
    for key, (extensions, profiles) in SCHEMAS_OF_PRESETS[name].items():
        defs = servers[name].schema(key)["$defs"]

        assert sorted(item for item in defs if item.startswith("ext.")) == sorted(extensions), (name, key)
        assert profile_defs({"$defs": defs}) == sorted(profiles), (name, key)
