"""The profiles of the demo extensions over the wire, on the demo backend (#179): each constraint of each profile has a request that
is accepted under a preset without the profile and refused under the preset with it, with 422 `02308` and the `profile` that owns
the constraint, and a member of an extension outside the signalled preset is a 400. The offers and the binding are a fixture of
this test; the demo configurations are #180's."""
import base64
import json
import sqlite3

import pytest
from starlette.testclient import TestClient

from tests.helper.demo_app import demo_composition

MEDIA_TYPE = "application/rpp+json"
SECRET = "Secret-Word1"
AUTH = {"Authorization": "Basic " + base64.b64encode(b"demo-a:demo-a-password").decode(), "Accept": MEDIA_TYPE,
        "Content-Type": MEDIA_TYPE, "RPP-Cltrid": "t-1"}


def profile_id(key):
    return f"org.example.rpp.profile.{key}"


@pytest.fixture(scope="module")
def composition(tmp_path_factory):
    database = tmp_path_factory.mktemp("demo") / "demo.db"
    composition = demo_composition(database, bound={"planets-atmosphere": ["habitable-atmospheres"]})
    yield composition, database
    composition.sessions.close()


@pytest.fixture
def app(composition):
    composition, database = composition
    with sqlite3.connect(database) as connection:
        for table in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN "
                                        "('schema_versions') AND name NOT LIKE 'sqlite_%'").fetchall():
            connection.execute(f"DELETE FROM {table[0]}")
    return Demo(TestClient(composition.app))


class Demo:
    def __init__(self, client):
        self.client = client

    def send(self, method, url, preset, body=None):
        headers = {**AUTH, "RPP-Preset": f"preset=org.example.rpp.preset.{preset};version=1.0"}
        return self.client.request(method, url, headers=headers, content=json.dumps(body) if body is not None else None)

    def planet(self, preset, name="mars", **members):
        return self.send("POST", "/planets", preset, planet(name, **members))

    def satellite(self, preset, name="phobos-i", **members):
        return self.send("POST", "/satellites", preset, satellite(name, **members))


def planet(name="mars", **members):
    body = {"@type": "planet", "id": name, "type": "rocky", "radius": 3389.5,
            "authInfo": {"@type": "authInfo", "method": "authinfo", "authdata": SECRET}, **members}
    return {key: value for key, value in body.items() if value is not None}


def satellite(name="phobos-i", of="mars", **members):
    return {"@type": "satellite", "id": name, "planet": {"@type": "planet", "id": of}, "orbitalPeriod": 0.32, **members}


def atmosphere(pressure=1.0, **members):
    return {"@type": "atmosphere", "pressure": pressure, **members}


def update(**members):
    body = {"@type": "planet", "type": "rocky", "radius": 3389.5, **members}
    return {key: value for key, value in body.items() if value is not None}


def refused_by(response, profile):
    assert response.status_code == 422, response.text
    error = response.json()["errors"][0]
    assert response.headers["RPP-Code"] == "02308" and error["result"] == "02308"
    assert error["profile"] == profile_id(profile)
    return error


def replace(path, value):
    return [{"op": "replace", "path": path, "value": value}]


def remove(path):
    return [{"op": "remove", "path": path}]


# --- rocky-planets: the type of a planet is rocky

def test_rocky_planets_refuses_another_type_on_create_and_the_same_request_is_accepted_without_the_profile(app):
    refused_by(app.planet("catalogued-planets", type="gas-giant"), "rocky-planets")
    assert app.planet("planets", type="gas-giant").status_code == 201


def test_rocky_planets_refuses_another_type_on_a_full_update(app):
    assert app.planet("catalogued-planets").status_code == 201

    refused_by(app.send("PUT", "/planets/mars", "catalogued-planets", update(type="ice-giant")), "rocky-planets")
    assert app.send("PUT", "/planets/mars", "planets", update(type="ice-giant")).status_code == 200


def test_rocky_planets_refuses_another_type_on_a_partial_update(app):
    assert app.planet("catalogued-planets").status_code == 201

    refused_by(app.send("PATCH", "/planets/mars", "catalogued-planets", replace("/type", "gas-giant")), "rocky-planets")
    assert app.send("PATCH", "/planets/mars", "planets", replace("/type", "gas-giant")).status_code == 200


# --- catalogued-satellites: the id of a satellite is a name and a roman numeral

def test_catalogued_satellites_refuses_an_id_that_is_no_designation(app):
    assert app.planet("planets").status_code == 201

    refused_by(app.satellite("catalogued-planets", "moon"), "catalogued-satellites")
    assert app.satellite("planets", "moon").status_code == 201
    assert app.satellite("catalogued-planets", "kepler-22b-iii").status_code == 201


# --- habitable-atmospheres: an atmosphere of 0.5 to 2 bar is required (bound to planets-atmosphere; planets-complete has none)

def test_habitable_atmospheres_requires_the_atmosphere_on_create_and_a_full_update(app):
    refused_by(app.planet("planets-atmosphere"), "habitable-atmospheres")
    assert app.planet("planets-complete").status_code == 201
    assert app.planet("planets-atmosphere", "venus", atmosphere=atmosphere(1.0)).status_code == 201

    refused_by(app.send("PUT", "/planets/venus", "planets-atmosphere", update()), "habitable-atmospheres")
    assert app.send("PUT", "/planets/mars", "planets-complete", update()).status_code == 200


def test_habitable_atmospheres_refuses_the_removal_of_the_atmosphere_that_it_requires(app):
    assert app.planet("planets-atmosphere", atmosphere=atmosphere(1.0)).status_code == 201

    error = refused_by(app.send("PATCH", "/planets/mars", "planets-atmosphere", remove("/atmosphere")),
                       "habitable-atmospheres")
    assert error["paths"] == ["$.atmosphere"] and "requires 'atmosphere'" in error["reason"]
    assert "atmosphere" in app.send("GET", "/planets/mars", "planets-atmosphere").json()
    assert app.send("PATCH", "/planets/mars", "planets-complete", remove("/atmosphere")).status_code == 200


@pytest.mark.parametrize("pressure", [0.1, 5])
def test_habitable_atmospheres_refuses_a_pressure_outside_its_range(app, pressure):
    refused_by(app.planet("planets-atmosphere", atmosphere=atmosphere(pressure)), "habitable-atmospheres")
    assert app.planet("planets-complete", atmosphere=atmosphere(pressure)).status_code == 201


def test_habitable_atmospheres_refuses_a_pressure_outside_its_range_on_a_partial_update(app):
    assert app.planet("planets-atmosphere", atmosphere=atmosphere(1.0)).status_code == 201

    refused_by(app.send("PATCH", "/planets/mars", "planets-atmosphere", replace("/atmosphere", atmosphere(5))),
               "habitable-atmospheres")
    assert app.send("PATCH", "/planets/mars", "planets-complete", replace("/atmosphere", atmosphere(5))).status_code == 200


# --- habitable-rocky-planets: builds on rocky-planets and habitable-atmospheres, and requires the radius

def test_habitable_rocky_planets_requires_the_radius_and_names_itself(app):
    refused_by(app.planet("habitable-worlds", radius=None, atmosphere=atmosphere(1.0)), "habitable-rocky-planets")
    assert app.planet("planets-atmosphere", radius=None, atmosphere=atmosphere(1.0)).status_code == 201

    refused_by(app.send("PUT", "/planets/mars", "habitable-worlds", update(radius=None, atmosphere=atmosphere(1.0))),
               "habitable-rocky-planets")
    assert app.send("PUT", "/planets/mars", "planets-atmosphere", update(radius=None, atmosphere=atmosphere(1.0))).status_code == 200


def test_habitable_rocky_planets_refuses_the_removal_of_the_radius(app):
    assert app.planet("habitable-worlds", atmosphere=atmosphere(1.0)).status_code == 201

    refused_by(app.send("PATCH", "/planets/mars", "habitable-worlds", remove("/radius")), "habitable-rocky-planets")
    assert app.send("PATCH", "/planets/mars", "planets-atmosphere", remove("/radius")).status_code == 200


def test_the_constraints_of_the_base_profiles_apply_and_name_their_own_profile(app):
    refused_by(app.planet("habitable-worlds", type="gas-giant", atmosphere=atmosphere(1.0)), "rocky-planets")
    refused_by(app.planet("habitable-worlds"), "habitable-atmospheres")
    refused_by(app.planet("habitable-worlds", atmosphere=atmosphere(9.0)), "habitable-atmospheres")
    assert app.planet("habitable-worlds", atmosphere=atmosphere(1.0)).status_code == 201


def test_a_satellite_of_habitable_worlds_needs_a_designation_through_the_preset_it_builds_on(app):
    assert app.planet("habitable-worlds", atmosphere=atmosphere(1.0)).status_code == 201

    refused_by(app.satellite("habitable-worlds", "moon"), "catalogued-satellites")
    assert app.satellite("habitable-worlds", "moon-i").status_code == 201


# --- a member of an extension outside the signalled preset is a 400

@pytest.mark.parametrize("preset", ["planets", "planets-orbits", "catalogued-planets"])
def test_an_atmosphere_outside_the_preset_is_400_on_create_a_full_update_and_a_partial_update(app, preset):
    assert app.planet("planets-complete").status_code == 201

    create = app.planet(preset, "venus", atmosphere=atmosphere())
    full = app.send("PUT", "/planets/mars", preset, update(atmosphere=atmosphere()))
    partial = app.send("PATCH", "/planets/mars", preset, replace("/atmosphere", atmosphere()))

    for response in (create, full, partial):
        assert response.status_code == 400 and response.headers["RPP-Code"] == "02001", response.text
    assert app.send("GET", "/planets/venus", "planets").status_code == 404
    assert "atmosphere" not in app.send("GET", "/planets/mars", "planets-complete").json()


def test_an_orbit_outside_the_preset_is_400(app):
    assert app.planet("planets").status_code == 201
    orbit = {"@type": "orbit", "semiMajorAxis": 9376}

    for preset in ("planets", "planets-atmosphere"):
        assert app.satellite(preset, "phobos-i", orbit=orbit).status_code == 400
    assert app.satellite("planets-orbits", "phobos-i", orbit=orbit).status_code == 201
    assert app.send("PUT", "/satellites/phobos-i", "planets", {"@type": "satellite", "orbit": orbit}).status_code == 400
    assert app.send("PATCH", "/satellites/phobos-i", "planets", replace("/orbit", orbit)).status_code == 400


# --- the members of the extensions

def test_an_atmosphere_is_created_read_replaced_changed_and_removed(app):
    created = app.planet("planets-complete", atmosphere=atmosphere(0.006, dominantGas="co2"))
    assert created.status_code == 201 and created.json()["atmosphere"] == atmosphere(0.006, dominantGas="co2")

    assert app.send("GET", "/planets/mars", "planets-atmosphere").json()["atmosphere"]["pressure"] == 0.006
    changed = app.send("PATCH", "/planets/mars", "planets-complete", replace("/atmosphere", atmosphere(2.5)))
    assert changed.json()["atmosphere"] == atmosphere(2.5)
    replaced = app.send("PUT", "/planets/mars", "planets-complete", update(atmosphere=atmosphere(3.0)))
    assert replaced.json()["atmosphere"] == atmosphere(3.0)
    assert "atmosphere" not in app.send("PATCH", "/planets/mars", "planets-complete", remove("/atmosphere")).json()


def test_an_atmosphere_with_a_negative_pressure_or_a_deeper_path_is_refused(app):
    assert app.planet("planets-complete", atmosphere=atmosphere(1.0)).status_code == 201

    assert app.planet("planets-complete", "venus", atmosphere=atmosphere(-1)).status_code == 400
    assert app.send("PATCH", "/planets/mars", "planets-complete", replace("/atmosphere/pressure", 2)).status_code == 400


def test_a_full_update_under_a_preset_without_the_extension_keeps_its_members_and_one_with_it_removes_them(app):
    assert app.planet("planets-complete", atmosphere=atmosphere(1.0)).status_code == 201

    kept = app.send("PUT", "/planets/mars", "planets", update(radius=1.0))
    assert kept.status_code == 200 and "atmosphere" not in kept.json()
    assert app.send("GET", "/planets/mars", "planets-atmosphere").json()["atmosphere"] == atmosphere(1.0)

    removed = app.send("PUT", "/planets/mars", "planets-complete", update(radius=1.0))
    assert removed.status_code == 200 and "atmosphere" not in removed.json()
    assert "atmosphere" not in app.send("GET", "/planets/mars", "planets-atmosphere").json()


def test_an_orbit_is_created_read_replaced_changed_and_removed_and_a_planet_with_its_satellites_keeps_them(app):
    orbit = {"@type": "orbit", "semiMajorAxis": 9376.0, "eccentricity": 0.015, "inclination": 1.1}
    assert app.planet("planets-complete").status_code == 201
    created = app.satellite("planets-complete", "phobos-i", orbit=orbit)
    assert created.status_code == 201 and created.json()["orbit"] == orbit

    patched = app.send("PATCH", "/satellites/phobos-i", "planets-complete", replace("/orbit", {**orbit, "inclination": 2}))
    assert patched.json()["orbit"]["inclination"] == 2
    replaced = app.send("PUT", "/satellites/phobos-i", "planets-orbits", {"@type": "satellite", "orbit": {**orbit, "eccentricity": 0.1}})
    assert replaced.json()["orbit"]["eccentricity"] == 0.1
    kept = app.send("PUT", "/satellites/phobos-i", "planets", {"@type": "satellite", "orbitalPeriod": 1})
    assert "orbit" not in kept.json()
    assert app.send("GET", "/satellites/phobos-i", "planets-orbits").json()["orbit"]["eccentricity"] == 0.1
    assert "orbit" not in app.send("PATCH", "/satellites/phobos-i", "planets-orbits", remove("/orbit")).json()
    assert app.send("DELETE", "/satellites/phobos-i", "planets-orbits").status_code == 200


def test_an_orbit_that_breaks_a_bound_is_400(app):
    assert app.planet("planets-complete").status_code == 201

    for orbit in ({"@type": "orbit", "semiMajorAxis": 0}, {"@type": "orbit", "semiMajorAxis": 1, "eccentricity": 1},
                  {"@type": "orbit", "semiMajorAxis": 1, "inclination": 181}, {"@type": "orbit"}):
        assert app.satellite("planets-orbits", "phobos-i", orbit=orbit).status_code == 400


def test_the_members_are_deleted_with_the_planet_and_a_planet_deleted_leaves_none_for_the_next(app):
    assert app.planet("planets-complete", atmosphere=atmosphere(1.0)).status_code == 201
    assert app.send("DELETE", "/planets/mars", "planets-complete").status_code == 200

    assert app.planet("planets-complete").json().get("atmosphere") is None


# --- a response shows the members of the extensions of the response's preset (media-type signalling)

def typed(key):
    return f"{MEDIA_TYPE};preset=org.example.rpp.preset.{key};preset-version=1.0"


@pytest.fixture(scope="module")
def media_type_app(tmp_path_factory):
    composition = demo_composition(tmp_path_factory.mktemp("demo") / "demo.db", signalling="media-type")
    yield TestClient(composition.app)
    composition.sessions.close()


def media(client, method, url, request_preset, response_preset, body=None):
    # the Accept lists the request preset too (else 400), with a lower weight, and the response preset the client prefers
    accept = typed(response_preset) if response_preset == request_preset else f"{typed(request_preset)};q=0.1, {typed(response_preset)}"
    headers = {**AUTH, "Content-Type": typed(request_preset), "Accept": accept}
    return client.request(method, url, headers=headers, content=json.dumps(body) if body is not None else None)


def test_a_response_shows_the_members_of_the_response_preset_and_not_those_of_the_request_preset(media_type_app):
    created = media(media_type_app, "POST", "/planets", "planets-complete", "planets", planet("venus", atmosphere=atmosphere()))
    assert created.status_code == 201 and "atmosphere" not in created.json()

    assert "atmosphere" not in media(media_type_app, "GET", "/planets/venus", "planets-complete", "planets").json()
    assert "atmosphere" not in media(media_type_app, "PUT", "/planets/venus", "planets-complete", "planets",
                                     update(atmosphere=atmosphere())).json()
    assert "atmosphere" not in media(media_type_app, "PATCH", "/planets/venus", "planets-complete", "planets",
                                     replace("/atmosphere", atmosphere())).json()


def test_a_response_shows_the_members_of_the_response_preset_also_where_the_request_preset_lacks_them(media_type_app):
    assert media(media_type_app, "POST", "/planets", "planets-complete", "planets-complete",
                 planet("mars", atmosphere=atmosphere(2.0))).status_code == 201

    read = media(media_type_app, "GET", "/planets/mars", "planets", "planets-complete")
    assert read.status_code == 200 and read.json()["atmosphere"] == atmosphere(2.0)
    kept = media(media_type_app, "PUT", "/planets/mars", "planets", "planets-complete", update(radius=1.0))
    assert kept.json()["atmosphere"] == atmosphere(2.0)


def test_the_same_holds_for_the_orbit_of_a_satellite(media_type_app):
    assert media(media_type_app, "POST", "/planets", "planets-complete", "planets-complete", planet("earth")).status_code == 201
    orbit = {"@type": "orbit", "semiMajorAxis": 384400}
    created = media(media_type_app, "POST", "/satellites", "planets-complete", "planets", satellite("moon-i", "earth", orbit=orbit))
    assert created.status_code == 201 and "orbit" not in created.json()

    assert "orbit" not in media(media_type_app, "GET", "/satellites/moon-i", "planets-complete", "planets").json()
    assert media(media_type_app, "GET", "/satellites/moon-i", "planets", "planets-complete").json()["orbit"] == orbit
    assert "orbit" not in media(media_type_app, "GET", "/planets/earth/satellites/moon-i", "planets-complete", "planets").json()
