"""The Preset Schema of each offered preset (json §Preset Schema): built once with the app, published at
/presets/{id}/schema in its native media type, and the schema the server validates with."""
import copy
import json
from urllib.parse import quote

import pytest
from jsonschema import Draft202012Validator

from core.session.session_pool import SessionPool
from rpp.http.app import create_app
from rpp.schema.effective_schema import UNEVALUATED
from tests.helper.epp_backends import epp_backends
from tests.helper.fake_epp_client import FakeEppClient
from tests.helper.fake_rri_client import FakeRriClient, rri_backends
from tests.helper.preset_fixtures import ADMIN_ONLY, AT_MOST_ONE, BASE, definitions_with, preset, registry_with
from tests.helper.presets import BASE as BASE_ID, EPP, RRI
from tests.helper.profiles import EPP_PROFILE, RRI_PROFILE
from tests.unit.test_presets_wire import epp_client, rri_client
from tests.unit.test_rri_wire import DISCOVERY

SCHEMA = {"Accept": "application/schema+json"}      # a schema fetch: no RPP-Cltrid, no preset, no authentication
BASE_URL = DISCOVERY.rpp_base_url


def url_of(identifier):
    return f"{BASE_URL}/presets/{quote(identifier, safe=':')}/schema"


def schema_of(client, identifier):
    response = client.get(f"/presets/{quote(identifier, safe='')}/schema", headers=SCHEMA)
    assert response.status_code == 200, response.text
    return response.json()


def fixture_client(presets, profiles, offered, default, bound=None, signalling="header"):
    registry = registry_with(presets, profiles)
    profile = EPP_PROFILE.with_changes({"presets": offered, "default_preset": default, "bound_profiles": bound or {}})
    sessions = SessionPool(epp_backends(lambda username, password: FakeEppClient(username, password)))
    return create_app(sessions, profile, discovery_settings=DISCOVERY, registry=registry, signalling=signalling).test_client()


def external_refs(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and not value.startswith("#/$defs/"):
                yield value
            else:
                yield from external_refs(value)
    elif isinstance(node, list):
        for item in node:
            yield from external_refs(item)


@pytest.mark.parametrize("client_of, identifiers", [(epp_client, [BASE_ID, EPP]), (rri_client, [BASE_ID, RRI])])
def test_each_offered_schema_is_a_valid_2020_12_self_contained_document_without_authentication(client_of, identifiers):
    client = client_of()
    for identifier in identifiers:
        response = client.get(f"/presets/{quote(identifier, safe='')}/schema", headers=SCHEMA)
        document = response.json()

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/schema+json"
        assert response.headers["RPP-Code"] == "01000"
        assert document["$id"] == url_of(identifier)
        assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert document["rpp:preset"] == {"id": identifier, "version": "1.0"}
        Draft202012Validator.check_schema(document)
        assert list(external_refs(document)) == []      # json §Preset Schema: MUST be self-contained


def test_the_id_is_the_url_of_the_sub_resource_with_the_colons_of_the_urn_as_json_shows_it():
    document = schema_of(epp_client(), EPP)

    assert document["$id"] == "https://rpp.example/presets/urn:ietf:params:rpp:preset:epp-compatible/schema"


def test_the_published_schema_has_no_unevaluated_properties_keyword_the_validator_adds_them():
    document = schema_of(epp_client(), EPP)

    # the bundle's own definitions may state it (the generated Card does), the composition adds none
    holder = document["$defs"]["restoreReport.create"]
    assert UNEVALUATED not in holder and set(holder) == {"allOf"}


def test_a_definition_a_profile_constrains_is_the_allof_of_the_base_in_place_and_the_profile_reference():
    document = schema_of(epp_client(), EPP)
    base = schema_of(epp_client(), BASE_ID)

    composed = document["$defs"]["restoreReport.create"]["allOf"]
    assert composed[0] == base["$defs"]["restoreReport.create"]
    assert composed[1] == {"$ref": "#/$defs/profile.restoreReport"}
    assert document["$defs"]["profile.restoreReport"]["properties"]["statements"] == {"minItems": 2}
    assert "profile.restoreReport" not in base["$defs"]       # the base preset has no applicable profile


def test_the_schema_of_a_preset_has_the_extension_in_place_and_not_in_another_preset():
    rri = schema_of(rri_client(), RRI)
    base = schema_of(rri_client(), BASE_ID)

    assert rri["$defs"]["domainName.create"]["allOf"][1] == {"$ref": "#/$defs/ext.rri.domainName.create"}
    assert "ext.rri.domainName.create" in rri["$defs"] and "ext.rri.domainName.create" not in base["$defs"]


def validator_of(document, definition):
    """What a client does with the published schema: adds the unevaluatedProperties the draft says a validator adds
    (here by the same function the server uses), and validates."""
    from rpp.schema.effective_schema import _inject      # noqa: PLC0415 - the one place a test needs the injection

    defs = copy.deepcopy(document["$defs"])
    holders = {name for name, value in defs.items() if set(value) == {"allOf"}}
    for name, value in defs.items():
        _inject(value, root=name not in holders and not name.startswith("profile."))
    for name in holders:
        defs[name][UNEVALUATED] = False
    return Draft202012Validator({"$ref": f"#/$defs/{definition}", "$defs": defs})


REPORT = {"@type": "restoreReport", "preData": "a", "postData": "b", "deleteTime": "2025-01-10T12:00:00Z",
          "restoreTime": "2025-01-20T15:30:00Z", "restoreReason": "r", "statements": ["x", "y"]}


def test_the_published_schema_decides_as_the_server_does():
    client = epp_client()
    constrained, plain = schema_of(client, EPP), schema_of(client, BASE_ID)
    one_statement = {**REPORT, "statements": ["only one"]}

    assert validator_of(constrained, "restoreReport.create").is_valid(REPORT)
    assert not validator_of(constrained, "restoreReport.create").is_valid(one_statement)
    assert validator_of(plain, "restoreReport.create").is_valid(one_statement)
    assert not validator_of(plain, "restoreReport.create").is_valid({**REPORT, "surprise": 1})


@pytest.mark.parametrize("name", ["nope", RRI])
def test_an_identifier_the_server_does_not_offer_is_a_404(name):
    response = epp_client().get(f"/presets/{quote(name, safe='')}/schema", headers=SCHEMA)

    assert response.status_code == 404 and response.headers["RPP-Code"] == "02303"
    assert response.headers["Content-Type"] == "application/problem+json"


def media_client():
    sessions = SessionPool(epp_backends(lambda username, password: FakeEppClient(username, password)))
    return create_app(sessions, EPP_PROFILE, discovery_settings=DISCOVERY, signalling="media-type").test_client()


@pytest.mark.parametrize("client_of", [epp_client, media_client], ids=["header", "media-type"])
class TestTheSchemaIsAValueInItsNativeMediaTypeOutsidePresetSignalling:
    def fetch(self, client_of, headers):
        return client_of().get(f"/presets/{BASE_ID}/schema", headers=headers)

    @pytest.mark.parametrize("accept", ["application/schema+json", "application/*", "*/*",
                                        "text/html, application/schema+json;q=0.5",
                                        'application/schema+json; preset="x"'])
    def test_an_accept_that_allows_the_document_is_answered(self, client_of, accept):
        response = self.fetch(client_of, {"Accept": accept})

        assert response.status_code == 200 and response.headers["Content-Type"] == "application/schema+json"
        assert response.headers["Vary"] == "Accept, Origin"

    def test_no_accept_is_any(self, client_of):
        assert client_of().get(f"/presets/{BASE_ID}/schema", headers={"Accept": ""}).status_code == 200

    @pytest.mark.parametrize("accept", ["text/html", "application/json", "application/rpp+json",
                                        "application/schema+json;q=0", "application/schema+json;q=0, application/json",
                                        "application/schema+json;q=0, */*"])      # the most specific range decides
    def test_an_accept_that_does_not_allow_it_is_a_406_problem_detail(self, client_of, accept):
        response = self.fetch(client_of, {"Accept": accept})

        assert response.status_code == 406 and response.headers["RPP-Code"] == "02004"
        assert response.headers["Content-Type"] == "application/problem+json"
        assert "RPP-Preset" not in response.headers

    def test_rpp_cltrid_is_optional_and_echoed_when_sent(self, client_of):
        assert "RPP-Cltrid" not in self.fetch(client_of, SCHEMA).headers
        assert self.fetch(client_of, {**SCHEMA, "RPP-Cltrid": "cl-9"}).headers["RPP-Cltrid"] == "cl-9"

    @pytest.mark.parametrize("headers", [
        {"RPP-Preset": "garbage"},                                          # no refusal, and nothing selected
        {"RPP-Preset": f"preset={RRI};version=9.9"},
        {"Content-Type": 'application/rpp+json; preset="nope"; preset-version="9.9"'},
        {"Accept": 'application/schema+json; preset="nope"; preset-version="9.9"'},
    ])
    def test_preset_headers_and_parameters_are_ignored(self, client_of, headers):
        response = self.fetch(client_of, {**SCHEMA, **headers})

        assert response.status_code == 200
        assert "RPP-Preset" not in response.headers
        assert response.headers["Content-Type"] == "application/schema+json"      # no preset parameters


def test_the_schema_is_the_effective_schema_of_that_server_and_preset_with_the_bound_profiles():
    plain = preset("plain", base_presets=[BASE["id"]])
    client = fixture_client([plain], [ADMIN_ONLY, AT_MOST_ONE], ["plain"], "plain",
                            bound={"plain": ["at-most-one"]})

    document = schema_of(client, plain[0])
    composed = document["$defs"]["domainName.create"]["allOf"]

    # the bound profile and its base profile both apply, each once
    assert [part for part in composed[1:]] == [{"$ref": "#/$defs/profile.adminOnly"}, {"$ref": "#/$defs/profile.atMostOne"}]


def test_two_apps_of_one_process_with_different_bindings_have_different_schemas():
    plain = preset("plain", base_presets=[BASE["id"]])
    bound = fixture_client([plain], [ADMIN_ONLY], ["plain"], "plain", bound={"plain": ["admin-only"]})
    unbound = fixture_client([plain], [ADMIN_ONLY], ["plain"], "plain")

    assert "profile.adminOnly" in schema_of(bound, plain[0])["$defs"]
    assert "profile.adminOnly" not in schema_of(unbound, plain[0])["$defs"]
