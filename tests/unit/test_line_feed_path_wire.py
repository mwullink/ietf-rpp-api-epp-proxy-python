import pytest

from rpp.http.app import create_app
from tests.helper.profiles import EPP_PROFILE

RPP_ERROR = "urn:ietf:params:rpp:error"
HEADERS = {"Accept": "application/rpp+json", "RPP-Cltrid": "lf-1"}


class NoSessions:
    def session(self, username, password):
        raise AssertionError("a path with a line feed needs no session")


@pytest.fixture(scope="module")
def client():
    return create_app(NoSessions(), EPP_PROFILE).test_client()


@pytest.mark.parametrize("method, path", [
    ("GET", "/messages/a%0Ab"),
    ("DELETE", "/messages/a%0Ab"),
    ("GET", "/hosts/a%0Ab"),
])
def test_path_with_line_feed_is_an_unknown_path(client, method, path):
    response = client.request(method, path, headers=HEADERS)

    assert response.status_code == 404
    assert response.headers["Content-Type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == RPP_ERROR
    assert body["status"] == 404
    assert body["detail"] == "Not Found"
    assert body["errors"][0]["reason"] == "Not Found"
    assert body["errors"][0]["result"] == "02001"
    assert response.headers["RPP-Code"] == "02001"
    assert response.headers["RPP-Svtrid"]
    assert response.headers["RPP-Cltrid"] == "lf-1"


@pytest.mark.parametrize("path", ["/messages/a%0Db", "/messages/a%09b"])
def test_other_control_characters_are_not_caught_by_the_guard(client, path):
    # Routed as before: the request reaches security, which refuses the anonymous client with 401, not 404.
    response = client.get(path, headers=HEADERS)

    assert response.status_code == 401


@pytest.mark.parametrize("path", ["/ui/", "/openapi.json"])
def test_ui_and_document_paths_are_unaffected(client, path):
    assert client.get(path).status_code == 200
