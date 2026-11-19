"""#205: `api_docs` serves the OpenAPI documents it is given and the UI over them in front of an app, and passes every other
request to that app. It knows no RPP: the documents are plain dicts, the first the default one (`/openapi.json`), then one per
preset, named by `info.x-rpp-preset`."""
import json
import re

import pytest
import yaml
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from api_docs.docs_app import DocsApp


def doc(preset_id, title):
    return {"openapi": "3.1.0", "info": {"title": title, "version": "1", "x-rpp-preset": {"id": preset_id, "version": "1.0"}},
            "servers": [{"url": "https://localhost:8000"}], "paths": {}}


DOCUMENTS = (doc("urn:x:a", "default"), doc("urn:x:a", "a"), doc("urn:x:b", "b"))


class App:
    """The app behind: answers every request with its path, and records the lifespan it saw."""

    def __init__(self):
        self.lifespan = []

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                self.lifespan.append(message["type"])
                await send({"type": message["type"] + ".complete"})
                if message["type"] == "lifespan.shutdown":
                    return
        await JSONResponse({"app": scope["path"]})(scope, receive, send)


@pytest.fixture
def app():
    return App()


@pytest.fixture
def client(app):
    return TestClient(DocsApp(app, DOCUMENTS))


def test_the_default_document_is_the_first(client):
    assert client.get("/openapi.json").json()["info"]["title"] == "default"
    assert yaml.safe_load(client.get("/openapi.yaml").text)["info"]["title"] == "default"


def test_a_preset_document_by_its_id(client):
    assert client.get("/openapi/urn:x:b.json").json()["info"]["title"] == "b"
    response = client.get("/openapi/urn:x:a.yaml")

    assert response.headers["Content-Type"].startswith("text/yaml")
    assert yaml.safe_load(response.text)["info"]["title"] == "a"


def test_a_preset_without_a_document_is_404(client):
    assert client.get("/openapi/urn:x:c.json").status_code == 404


def test_the_servers_are_the_base_path_of_the_request(app):
    assert TestClient(DocsApp(app, DOCUMENTS)).get("/openapi.json").json()["servers"] == [{"url": ""}]
    behind = TestClient(DocsApp(app, DOCUMENTS), root_path="/rpp")

    assert behind.get("/rpp/openapi/urn:x:b.json").json()["servers"] == [{"url": "/rpp"}]


def test_the_documents_given_are_not_changed(app):
    documents = json.loads(json.dumps(DOCUMENTS))
    TestClient(DocsApp(app, documents)).get("/openapi.json")

    assert documents == json.loads(json.dumps(DOCUMENTS))


def test_a_document_may_be_read_from_another_origin(client):
    response = client.get("/openapi.json", headers={"Origin": "https://ui.example"})

    assert response.headers["Access-Control-Allow-Origin"] == "*"


def test_the_ui_has_a_source_per_preset_the_default_first(client):
    page = client.get("/ui/")
    found = re.search(r'<script id="rpp-ui-configuration" type="application/json">(.*?)</script>', page.text, re.DOTALL)
    sources = json.loads(found.group(1))["sources"]

    assert [source["url"] for source in sources] == ["/openapi/urn:x:a.json", "/openapi/urn:x:b.json"]
    assert sources[0]["default"] is True and "default" not in sources[1]
    assert client.get("/ui/standalone.js").status_code == 200


def test_the_ui_files_beside_the_page_are_not_served(client):
    for name in ("index.j2", "README.md", "LICENSE"):
        assert client.get(f"/ui/{name}").json() == {"app": f"/ui/{name}"}


def test_every_other_request_goes_to_the_app(client):
    for path in ("/domains/example.example", "/openapi", "/openapi.txt", "/.well-known/rpp"):
        assert client.get(path).json() == {"app": path}


def test_the_app_has_its_lifespan(app):
    with TestClient(DocsApp(app, DOCUMENTS)):
        pass

    assert app.lifespan == ["lifespan.startup", "lifespan.shutdown"]
