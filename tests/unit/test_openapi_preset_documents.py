"""#205: every offered preset has an OpenAPI document of its own (`/openapi/{preset-id}.json` and `.yaml`, outside the RPP
paths): OpenAPI 3.1 with that preset's body schemas, the same as `GET /presets/{id}/schema`, and the preset signalled the way the
server takes it, so that a client (and the UI) sends it. Header signalling: the document's `RPP-Preset` parameter is required, with
the preset as its only value. Media type signalling: every RPP body is keyed by the preset's media type, and there is no
`RPP-Preset` parameter. `/openapi.json` stays the default preset's (#204). `/ui/` is Scalar, with a document per offered preset and
nothing of Scalar's platform (no developer tools, AI, MCP, telemetry or remote fonts), snippets HTTP/1.1 and curl only."""
import json
import re
from urllib.parse import quote

import pytest
import yaml

from core.session.session_pool import SessionPool
from rpp.http.app import create_app
from tests.helper.api_docs import served_client
from tests.helper.openapi_documents import (
    MEDIA_TYPE,
    SCHEMAS,
    Server,
    assert_holds_the_preset_schema,
    assert_valid_openapi_3_1,
    definition,
    document,
    in_components,
    p,
    preset_defs,
)
from tests.helper.profiles import EPP_PROFILE

METHODS = ("get", "put", "post", "delete", "patch")
BASE = "urn:ietf:params:rpp:preset:base"
EPP_PRESETS = (BASE, "urn:ietf:params:rpp:preset:epp-compatible")  # src/settings/profiles/epp.yaml
ATMOSPHERE = {"@type": "atmosphere", "pressure": 1.0}


@pytest.fixture(scope="module")
def servers(tmp_path_factory):
    """extended: header signalling, default planets-complete; bound: media type signalling, default planets. Both leave out
    what a preset does not hold (`rpp_openapi_omit_*`)."""
    directory = tmp_path_factory.mktemp("openapi-presets")
    built = {name: Server(name, directory) for name in ("extended", "bound")}
    yield built
    for server in built.values():
        server.composition.sessions.close()


@pytest.fixture(scope="module")
def epp():
    return served_client(create_app(SessionPool(lambda username, password: None), EPP_PROFILE))


def offered(client):
    """The offered presets (id, version), as discovery states them."""
    response = client.get("/.well-known/rpp", headers={"Accept": MEDIA_TYPE, "RPP-Cltrid": "oas-discovery"})
    assert response.status_code == 200, response.text
    return [(item["id"], item["version"]) for item in response.json()["presets"]]


def preset_document(client, preset_id):
    response = client.get(f"/openapi/{quote(preset_id, safe=':')}.json")
    assert response.status_code == 200, response.text
    return response.json()


def resolved(doc, node):
    ref = node.get("$ref")
    if ref is None:
        return node
    section, name = ref.removeprefix("#/components/").split("/", 1)
    return doc["components"][section][name]


def operations(doc):
    for path, item in doc["paths"].items():
        for method in METHODS:
            if method in item:
                yield path, method, item[method]


def parameters(doc, operation):
    return [resolved(doc, parameter) for parameter in operation.get("parameters", [])]


def rpp_contents(operation):
    """The `content` maps of the operation's request and response bodies that hold an RPP body (not a Problem Detail)."""
    contents = [operation["requestBody"]["content"]] if "requestBody" in operation else []
    contents += [response["content"] for response in operation.get("responses", {}).values() if "content" in response]
    return [content for content in contents if any(key.startswith(MEDIA_TYPE) for key in content)]


def body_key(doc, path, method="post"):
    """The key of the request body's RPP media type."""
    keys = [key for key in doc["paths"][path][method]["requestBody"]["content"] if key.startswith(MEDIA_TYPE)]
    assert len(keys) == 1, keys
    return keys[0]


def request_schema(doc, path, method="post"):
    return doc["paths"][path][method]["requestBody"]["content"][body_key(doc, path, method)]["schema"]


def preset_parameter(doc, path, method="post"):
    found = [parameter for parameter in parameters(doc, doc["paths"][path][method]) if parameter["name"] == "RPP-Preset"]
    assert len(found) == 1, found
    return found[0]


def planet(name, **members):
    return {"@type": "planet", "id": name, "type": "rocky", "radius": 3389.5,
            "authInfo": {"@type": "authInfo", "method": "authinfo", "authdata": "Secret-Word1"}, **members}


# --- a document per offered preset, OpenAPI 3.1, naming its preset

@pytest.mark.parametrize("name", ["extended", "bound"])
def test_each_offered_preset_has_a_valid_openapi_3_1_document_naming_it(servers, name):
    client = servers[name].client
    for preset_id, version in offered(client):
        doc = preset_document(client, preset_id)
        assert doc["info"]["x-rpp-preset"] == {"id": preset_id, "version": version}
        assert_valid_openapi_3_1(doc)


def test_the_yaml_of_a_preset_is_the_same_document_as_its_json(servers):
    client = servers["extended"].client
    response = client.get(f"/openapi/{p('planets-atmosphere')}.yaml")

    assert response.status_code == 200
    assert yaml.safe_load(response.text) == preset_document(client, p("planets-atmosphere"))


def test_a_preset_that_is_not_offered_has_no_document(servers):
    assert servers["extended"].client.get(f"/openapi/{p('catalogued-planets')}.json").status_code == 404


# --- the body schemas are the preset's, the same as GET /presets/{id}/schema

@pytest.mark.parametrize("name", ["extended", "bound"])
def test_a_request_body_is_the_definition_of_the_documents_preset(servers, name):
    client = servers[name].client
    for preset in ("planets", "planets-atmosphere", "planets-complete"):
        doc = preset_document(client, p(preset))
        defs = preset_defs(client, p(preset))
        ref = request_schema(doc, "/planets")["$ref"]
        key = ref[len(SCHEMAS):]

        assert key in defs, (preset, key)
        assert definition(doc, ref) == in_components(defs[key])


def test_the_documents_of_two_presets_differ_by_their_extensions(servers):
    client = servers["extended"].client
    planets = preset_document(client, p("planets"))
    atmosphere = preset_document(client, p("planets-atmosphere"))

    assert "atmosphere" not in json.dumps(definition(planets, request_schema(planets, "/planets")["$ref"]))
    assert "atmosphere" in json.dumps(definition(atmosphere, request_schema(atmosphere, "/planets")["$ref"]))


def test_a_preset_document_holds_its_whole_preset_schema_where_nothing_is_left_out(epp):
    for preset_id in EPP_PRESETS:
        assert_holds_the_preset_schema(preset_document(epp, preset_id), preset_defs(epp, preset_id))


def test_a_preset_document_leaves_out_the_objects_of_extensions_its_preset_does_not_contain(servers):
    """A request to them under the preset is refused (400, core RC4): the base preset has no planets."""
    client = servers["bound"].client

    assert "/planets" not in preset_document(client, BASE)["paths"]
    assert "/planets" in preset_document(client, p("planets"))["paths"]


# --- header signalling: the document's RPP-Preset is its preset

def test_under_header_signalling_rpp_preset_is_required_with_the_documents_preset_alone(servers):
    doc = preset_document(servers["extended"].client, p("planets-atmosphere"))
    parameter = preset_parameter(doc, "/planets")

    assert parameter["required"] is True
    assert parameter["schema"]["enum"] == [parameter["schema"]["default"]]


def test_under_header_signalling_the_rpp_preset_of_a_document_selects_its_preset(servers):
    server = servers["extended"]
    doc = preset_document(server.client, p("planets-atmosphere"))
    value = preset_parameter(doc, "/planets")["schema"]["default"]
    headers = {**server.headers("planets"), "RPP-Preset": value}

    response = server.client.request("POST", "/planets", headers=headers,
                                     content=json.dumps(planet("oas-header", atmosphere=ATMOSPHERE)))

    assert response.status_code == 201, response.text
    assert p("planets-atmosphere") in response.headers["RPP-Preset"]


def test_under_header_signalling_the_bodies_keep_the_plain_media_type(servers):
    doc = preset_document(servers["extended"].client, p("planets-atmosphere"))

    assert body_key(doc, "/planets") == MEDIA_TYPE


def test_the_drafts_accept_parameter_stays(servers):
    doc = preset_document(servers["extended"].client, p("planets-atmosphere"))

    assert "Accept" in [parameter["name"] for parameter in parameters(doc, doc["paths"]["/planets"]["post"])]


# --- media type signalling: the bodies are keyed by the preset's media type

def test_under_media_type_signalling_every_rpp_body_is_keyed_by_the_documents_preset(servers):
    doc = preset_document(servers["bound"].client, p("planets-atmosphere"))
    pattern = re.compile(rf'^{re.escape(MEDIA_TYPE)}; preset="?{re.escape(p("planets-atmosphere"))}"?; preset-version="?1\.0"?$')

    keys = {key for _, _, operation in operations(doc) for content in rpp_contents(operation) for key in content
            if key.startswith(MEDIA_TYPE)}

    assert keys
    assert all(pattern.match(key) for key in keys), keys


def test_under_media_type_signalling_there_is_no_rpp_preset_parameter(servers):
    doc = preset_document(servers["bound"].client, p("planets-atmosphere"))

    names = [parameter["name"] for _, _, operation in operations(doc) for parameter in parameters(doc, operation)]
    names += [parameter["name"] for parameter in doc["components"].get("parameters", {}).values()]

    assert "RPP-Preset" not in names


def test_under_media_type_signalling_the_media_type_of_a_document_selects_its_preset(servers):
    server = servers["bound"]
    key = body_key(preset_document(server.client, p("planets-atmosphere")), "/planets")
    headers = {**server.headers("planets"), "Content-Type": key, "Accept": key}

    response = server.client.request("POST", "/planets", headers=headers,
                                     content=json.dumps(planet("oas-media", atmosphere=ATMOSPHERE)))

    assert response.status_code == 201, response.text
    assert response.headers["Content-Type"] == key


def content_type_parameters(doc, operation):
    return [parameter for parameter in parameters(doc, operation) if parameter["name"].lower() == "content-type"]


def test_under_media_type_signalling_an_operation_without_a_body_states_the_documents_preset_as_content_type(servers):
    """The request preset of a request without a body is that of its Content-Type too (core §13): without one it is the
    default preset. OAS 3.1 has a Content-Type header parameter ignored; Scalar sends it."""
    doc = preset_document(servers["bound"].client, p("planets-atmosphere"))
    key = body_key(doc, "/planets")
    bodyless = [(path, method, operation) for path, method, operation in operations(doc) if "requestBody" not in operation]

    assert bodyless
    for path, method, operation in bodyless:
        found = content_type_parameters(doc, operation)
        assert len(found) == 1, (path, method, found)
        assert found[0]["in"] == "header"
        assert found[0]["required"] is True
        assert found[0]["schema"]["enum"] == [key] and found[0]["schema"]["default"] == key
    for path, method, operation in operations(doc):
        if "requestBody" in operation:
            assert content_type_parameters(doc, operation) == [], (path, method)


def test_under_header_signalling_no_operation_has_a_content_type_parameter(servers):
    doc = preset_document(servers["extended"].client, p("planets-atmosphere"))

    assert all(content_type_parameters(doc, operation) == [] for _, _, operation in operations(doc))


def test_under_media_type_signalling_the_content_type_of_a_read_selects_the_documents_preset(servers):
    server = servers["bound"]
    doc = preset_document(server.client, p("planets-atmosphere"))
    key = content_type_parameters(doc, doc["paths"]["/planets/{id}"]["get"])[0]["schema"]["default"]
    created = server.client.request("POST", "/planets", headers={**server.headers("planets"), "Content-Type": key, "Accept": key},
                                    content=json.dumps(planet("oas-read", atmosphere=ATMOSPHERE)))
    assert created.status_code == 201, created.text

    plain = {name: value for name, value in server.headers("planets").items() if name != "Content-Type"}
    without = server.client.get("/planets/oas-read", headers={**plain, "Accept": key})
    response = server.client.get("/planets/oas-read", headers={**server.headers("planets"), "Content-Type": key, "Accept": key})

    assert without.status_code == 400, without.text
    assert response.status_code == 200, response.text
    assert response.headers["Content-Type"] == key


# --- /openapi.json stays the default preset's (#204)

def test_the_default_document_is_unchanged_by_the_signalling(servers):
    doc = document(servers["bound"].client)

    assert doc["info"]["x-rpp-preset"]["id"] == p("planets")
    assert body_key(doc, "/planets") == MEDIA_TYPE
    assert preset_parameter(doc, "/planets")["required"] is False


# --- /ui/ is Scalar with a document per preset and none of Scalar's platform

def ui_configuration(client):
    page = client.get("/ui/")
    assert page.status_code == 200
    found = re.search(r'<script id="rpp-ui-configuration" type="application/json">(.*?)</script>', page.text, re.DOTALL)
    assert found, page.text
    return page.text, json.loads(found.group(1))


def test_the_ui_offers_a_document_per_preset_the_default_first(servers):
    client = servers["bound"].client
    _, configuration = ui_configuration(client)

    urls = [source["url"] for source in configuration["sources"]]

    assert urls[0] == f"/openapi/{p('planets')}.json"
    assert sorted(urls) == sorted(f"/openapi/{preset_id}.json" for preset_id, _ in offered(client))
    for url in urls:
        assert client.get(url).status_code == 200


def test_the_ui_has_none_of_scalars_platform(epp):
    page, configuration = ui_configuration(epp)

    assert configuration["showDeveloperTools"] == "never"
    assert configuration["agent"] == {"disabled": True}
    assert configuration["mcp"] == {"disabled": True}
    assert configuration["telemetry"] is False
    assert configuration["withDefaultFonts"] is False
    assert ".open-api-client-button" in page
    assert not re.search(r"https?://", page)


def test_the_ui_offers_the_http_1_1_and_curl_snippets_only(epp):
    _, configuration = ui_configuration(epp)
    hidden = configuration["hiddenClients"]

    assert configuration["defaultHttpClient"] == {"targetKey": "http", "clientKey": "http1.1"}
    assert "http" not in hidden
    assert hidden["shell"] == ["httpie", "wget"]
    assert all(value is True for target, value in hidden.items() if target != "shell")


def test_the_ui_is_scalar_1_76_4_and_swagger_ui_is_gone(epp):
    bundle = epp.get("/ui/standalone.js")

    assert bundle.status_code == 200
    assert "`1.76.4`" in bundle.text
    assert epp.get("/ui/swagger-ui-bundle.js").status_code == 404
