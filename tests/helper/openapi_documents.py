"""The OpenAPI documents a deployment serves (#204, #205), and apps of the demo configurations (#180) to read them from."""
import base64
import dataclasses
import json
import re

from openapi_spec_validator import OpenAPIV31SpecValidator
from openapi_spec_validator.validation.exceptions import ExtraParametersError
from starlette.testclient import TestClient

from main import compose
from settings.load_settings import load_settings
from settings.sqlite_settings import SqliteSettings
from tests.helper.test_environment import REPOSITORY

MEDIA_TYPE = "application/rpp+json"
BASIC = "Basic " + base64.b64encode(b"demo-a:demo-a-password").decode()
SCHEMAS = "#/components/schemas/"

CONFIGS = {
    "bare": "config/environments/sqlite-demo.yaml", "extended": "config/environments/sqlite-demo-extended.yaml",
    "bound": "config/environments/sqlite-demo-bound.yaml",
    "inherit": "config/environments/sqlite-demo-inherit.yaml",
}


def p(key):
    return f"org.example.rpp.preset.{key}"


class Server:
    """An app composed from a demo configuration file, with a database file of its own."""

    def __init__(self, name, directory):
        settings = load_settings(str(REPOSITORY / CONFIGS[name]))
        settings = dataclasses.replace(settings, sqlite=SqliteSettings(
            rpp_sqlite_url=f"sqlite:///{directory / (name + '.db')}", rpp_sqlite_clients=settings.sqlite.rpp_sqlite_clients))
        self.composition = compose(settings)
        self.client = TestClient(self.composition.app)
        self.signalling = settings.preset_signalling
        self.default = settings.profile_layers[1]["default_preset"]
        self.counter = 0

    def headers(self, preset):
        self.counter += 1
        headers = {"Authorization": BASIC, "RPP-Cltrid": f"oas-{self.counter}"}
        if self.signalling == "header":
            headers.update({"Accept": MEDIA_TYPE, "Content-Type": MEDIA_TYPE, "RPP-Preset": f"preset={p(preset)};version=1.0"})
        else:
            typed = f'{MEDIA_TYPE}; preset="{p(preset)}"; preset-version="1.0"'
            headers.update({"Accept": typed, "Content-Type": typed})
        return headers

    def post(self, url, body, preset):
        return self.client.request("POST", url, headers=self.headers(preset), content=json.dumps(body))

    def get(self, url, preset):
        return self.client.get(url, headers=self.headers(preset))


def document(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    return response.json()


def preset_defs(client, preset_id):
    response = client.get(f"/presets/{preset_id}/schema", headers={"Accept": "application/schema+json"})
    assert response.status_code == 200, response.text
    return response.json()["$defs"]


def in_components(schema):
    """A definition of a Preset Schema as the OpenAPI document holds it: its references point into `components/schemas`."""
    return json.loads(re.sub(r'"#/\$defs/', f'"{SCHEMAS}', json.dumps(schema)))


def definition(doc, ref):
    assert ref.startswith(SCHEMAS), ref
    return doc["components"]["schemas"][ref[len(SCHEMAS):]]


def assert_holds_the_preset_schema(doc, defs):
    """Every definition of the Preset Schema is in the document, the same as published."""
    schemas = doc["components"]["schemas"]
    for key, schema in defs.items():
        assert key in schemas, key
        assert schemas[key] == in_components(schema), key


def assert_valid_openapi_3_1(doc):
    """Valid OpenAPI 3.1. `ExtraParametersError` is a check of the validator's own, not of the specification: a `required` that
    names a member another schema of an `allOf` declares, which a Profile Schema does (`profile.address` requires
    `countryCode`), is valid JSON Schema."""
    assert doc["openapi"] == "3.1.0"
    errors = [str(error) for error in OpenAPIV31SpecValidator(doc).iter_errors() if not isinstance(error, ExtraParametersError)]
    assert errors == []
