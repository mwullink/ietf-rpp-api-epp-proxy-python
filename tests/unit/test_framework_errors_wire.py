import pytest

from rpp.http.app import create_app
from tests.helper.profiles import EPP_PROFILE
from tests.unit.test_app_injection import OBJECT_DOES_NOT_EXIST, auth_header, client_for

MEDIA_TYPE = "application/rpp+json"
RPP_ERROR = "urn:ietf:params:rpp:error"
HEADERS = {"Accept": MEDIA_TYPE, "RPP-Cltrid": "fw-err-1"}


class NoSessions:
    def session(self, username, password):
        raise AssertionError("an error of the framework needs no session")


@pytest.fixture(scope="module")
def client():
    return create_app(NoSessions(), EPP_PROFILE).test_client()


def assert_rpp_error(response, status):
    assert response.status_code == status
    assert response.headers["Content-Type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == RPP_ERROR
    assert body["status"] == status
    assert body["errors"][0]["result"] == "02001"
    assert response.headers["RPP-Code"] == "02001"
    assert response.headers["RPP-Svtrid"]
    assert response.headers["RPP-Cltrid"] == "fw-err-1"


def allowed(response):
    return {m.strip() for m in response.headers["Allow"].split(",")}


def test_wrong_method_on_discovery_is_an_rpp_error_with_allow(client):
    response = client.post("/.well-known/rpp", headers=HEADERS)

    assert_rpp_error(response, 405)
    assert allowed(response) == {"GET", "HEAD"}
    body = response.json()
    assert body["title"] == "Method Not Allowed"
    assert body["detail"] == "Method Not Allowed"
    assert body["errors"][0]["reason"] == "Method Not Allowed"


def test_wrong_method_on_messages_is_an_rpp_error_with_allow(client):
    response = client.put("/messages", headers=HEADERS)

    assert_rpp_error(response, 405)
    assert allowed(response) == {"POST"}
    body = response.json()
    assert body["detail"] == "Method Not Allowed"
    assert body["errors"][0]["reason"] == "Method Not Allowed"


def test_unknown_path_is_an_rpp_error(client):
    response = client.get("/nonexistent", headers=HEADERS)

    assert_rpp_error(response, 404)
    body = response.json()
    assert body["title"] == "Not Found"
    assert isinstance(body["errors"][0]["reason"], str) and body["errors"][0]["reason"]


def test_problem_exception_is_still_rendered_by_its_own_handler():
    http, _ = client_for(reply=(False, "2303", OBJECT_DOES_NOT_EXIST))

    response = http.delete("/domainNames/missing.example", headers=auth_header("user", "pw"))

    assert response.status_code == 404
    assert response.headers["RPP-Code"] == "02303"
    body = response.json()
    assert body["type"] == RPP_ERROR
    assert body["title"] == "Object does not exist"
    assert body["errors"][0]["result"] == "02303"
