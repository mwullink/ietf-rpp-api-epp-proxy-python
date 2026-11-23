"""A profile constrains and a preset does not (#174, the proxy criteria): a request that breaks a constraint of an applicable
profile is 02308 (422) naming the profile, the same request under a preset without the profile is not refused for it, and a
request that fails the preset schema stays 400. Over the wire, with presets and profiles an extension brings."""
import base64

import pytest

from core.session.session_pool import SessionPool
from rpp.http.app import create_app
from tests.helper.epp_backends import epp_backends
from tests.helper.fake_epp_client import FakeEppClient
from tests.helper.preset_fixtures import (
    ADMIN_ONLY, AT_MOST_ONE, AUTH_REQUIRED, BASE, ONE_NAMESERVER, SHORT_EMAIL, preset, registry_with)
from tests.helper.profiles import EPP_PROFILE
from tests.unit.test_contact_put_wire import info as contact_info
from tests.unit.test_domain_put_wire import DONE, info
from tests.unit.test_rri_wire import DISCOVERY

MEDIA_TYPE = "application/rpp+json"
AUTH = {"Authorization": "Basic " + base64.b64encode(b"user:pw").decode(), "Accept": MEDIA_TYPE,
        "Content-Type": MEDIA_TYPE, "RPP-Cltrid": "cl-1"}

PLAIN = preset("plain", base_presets=[BASE["id"]])
CONSTRAINED = preset("constrained", base_presets=[BASE["id"]], profiles=[ADMIN_ONLY[0]])
LIMITED = preset("limited", base_presets=[BASE["id"]], profiles=[ONE_NAMESERVER[0]])
SHORT = preset("short", base_presets=[BASE["id"]], profiles=[SHORT_EMAIL[0]])
PROFILES = [ADMIN_ONLY, AT_MOST_ONE, AUTH_REQUIRED, ONE_NAMESERVER, SHORT_EMAIL]
PRESETS = [PLAIN, CONSTRAINED, LIMITED, SHORT]


def epp_reply(code=1000):
    return (True, str(code), '<epp xmlns="urn:ietf:params:xml:ns:epp-1.0"><response><result code="%d"><msg>m</msg></result>'
                             '<trID><clTRID>cl-1</clTRID><svTRID>sv-1</svTRID></trID></response></epp>' % code)


class App:
    def __init__(self, bound=None, offered=("plain", "constrained", "limited", "short"), default="plain", signalling="header",
                 replies=(), informational=()):
        self.clients = []

        def factory(username, password):
            client = FakeEppClient(username, password, reply=epp_reply(), replies=list(replies))
            self.clients.append(client)
            return client
        profile = EPP_PROFILE.with_changes({"presets": list(offered), "default_preset": default,
                                            "bound_profiles": bound or {}, "informational_profiles": list(informational)})
        self.http = create_app(SessionPool(epp_backends(factory)), profile, discovery_settings=DISCOVERY,
                               registry=registry_with(PRESETS, PROFILES), signalling=signalling).test_client()

    def sent(self):
        return [message for client in self.clients for message in client.sent]

    def create(self, body, preset_key="plain", extra=None):
        headers = {**AUTH, "RPP-Preset": f"preset=org.example.rpp.preset.{preset_key};version=1.0", **(extra or {})}
        return self.http.post("/domainNames", json=body, headers=headers)


def domain(*labels, **more):
    return {"@type": "domainName", "name": "foo.example",
            "contacts": [{"label": label, "object": {"@type": "contact", "id": "C-1"}} for label in labels], **more}


def test_a_request_that_breaks_a_profile_constraint_is_422_with_the_profile_and_the_path():
    app = App()

    response = app.create(domain("billing"), "constrained")

    assert response.status_code == 422
    assert response.headers["RPP-Code"] == "02308"
    error = response.json()["errors"][0]
    assert error["result"] == "02308" and error["profile"] == ADMIN_ONLY[0]
    assert error["paths"] == ["$.contacts[0].label"]
    assert "billing" not in response.text.replace("billing", "", 0) or "billing" not in error["reason"]   # no value of the request
    assert app.sent() == []


def test_the_same_request_is_not_refused_for_the_profile_under_a_preset_without_it():
    app = App()

    response = app.create(domain("billing"), "plain")

    assert response.status_code not in (400, 422), response.text
    assert app.sent()       # it went on to the backend


def test_a_request_the_profile_allows_goes_on_under_the_preset_that_has_it():
    app = App()

    assert app.create(domain("admin"), "constrained").status_code not in (400, 422)
    assert app.sent()


def test_a_request_that_fails_the_preset_schema_stays_400_whatever_the_profile_says():
    app = App()
    undeclared = app.create({**domain("billing"), "surprise": 1}, "constrained")
    wrong_type = app.create({**domain("billing"), "contacts": "x"}, "constrained")

    assert undeclared.status_code == 400 and undeclared.headers["RPP-Code"] == "02001"
    assert wrong_type.status_code == 400
    assert app.sent() == []


def test_a_bound_profile_applies_like_one_of_the_definition_and_its_base_profile_with_it():
    app = App(bound={"plain": ["at-most-one"]})

    too_many = app.create(domain("admin", "admin"), "plain")
    wrong_label = app.create(domain("tech"), "plain")

    assert too_many.status_code == 422 and too_many.json()["errors"][0]["profile"] == AT_MOST_ONE[0]
    assert wrong_label.status_code == 422 and wrong_label.json()["errors"][0]["profile"] == ADMIN_ONLY[0]
    assert app.create(domain("admin"), "plain").status_code not in (400, 422)


def test_the_binding_is_the_servers_and_another_preset_of_it_is_not_constrained_by_it():
    app = App(bound={"plain": ["auth-required"]})

    assert app.create(domain("admin"), "plain").status_code == 422       # the bound profile requires authInfo
    assert app.create(domain("admin"), "constrained").status_code not in (400, 422)   # a preset without the binding


LIMITED_HEADERS = {**AUTH, "RPP-Preset": f"preset={LIMITED[0]};version=1.0"}
TWO = [{"@type": "host", "hostName": "ns1.foo.example"}, {"@type": "host", "hostName": "ns2.foo.example"}]


def test_a_full_update_that_breaks_a_profile_constraint_is_422_and_one_that_keeps_it_goes_on():
    refused = App()
    refused_response = refused.http.put("/domainNames/foo.example", json={"@type": "domainName", "nameservers": TWO},
                                        headers=LIMITED_HEADERS)
    accepted = App(replies=[info("ns2.foo.example"), DONE, info("ns1.foo.example")])
    accepted_response = accepted.http.put("/domainNames/foo.example", json={"@type": "domainName", "nameservers": TWO[:1]},
                                          headers=LIMITED_HEADERS)

    assert refused_response.status_code == 422 and refused_response.headers["RPP-Code"] == "02308"
    assert refused_response.json()["errors"][0]["profile"] == ONE_NAMESERVER[0]
    assert refused.sent() == []
    assert accepted_response.status_code == 200


def test_a_patch_is_checked_on_the_object_it_results_in_so_what_it_adds_to_what_is_there_is_422():
    app = App(replies=[info("ns1.foo.example")])
    add = [{"op": "add", "path": "/nameservers", "value": TWO[1]}]

    response = app.http.patch("/domainNames/foo.example", json=add, headers=LIMITED_HEADERS)

    assert response.status_code == 422 and response.headers["RPP-Code"] == "02308"
    assert response.json()["errors"][0]["profile"] == ONE_NAMESERVER[0]
    assert len(app.sent()) == 1 and "domain:info" in app.sent()[0]         # the read for it, and no update


def test_the_same_patch_under_a_preset_without_the_profile_goes_on():
    app = App(replies=[DONE, info("ns1.foo.example", "ns2.foo.example")])      # no profile: no read for the patch
    add = [{"op": "add", "path": "/nameservers", "value": TWO[1]}]

    response = app.http.patch("/domainNames/foo.example", json=add, headers=AUTH)       # the default preset has none

    assert response.status_code == 200


@pytest.mark.parametrize("signalling", ["header", "media-type"])
def test_the_preset_is_signalled_by_the_header_or_the_media_type_parameters_as_the_server_is_set(signalling):
    app = App(signalling=signalling)
    if signalling == "header":
        response = app.create(domain("billing"), "constrained")
    else:
        typed = f'{MEDIA_TYPE}; preset="{CONSTRAINED[0]}"; preset-version="1.0"'
        response = app.http.post("/domainNames", json=domain("billing"),
                                 headers={**AUTH, "Accept": typed, "Content-Type": typed})

    assert response.status_code == 422 and response.json()["errors"][0]["profile"] == ADMIN_ONLY[0]


def test_without_a_signal_the_default_preset_applies_in_both_methods():
    for signalling in ("header", "media-type"):
        app = App(default="constrained", signalling=signalling)

        response = app.http.post("/domainNames", json=domain("billing"), headers=AUTH)

        assert response.status_code == 422, signalling


def test_a_preset_or_version_the_server_does_not_offer_is_refused_with_the_code_of_the_signalling():
    app = App(offered=("plain",))

    unknown = app.create(domain("admin"), "constrained")
    version = app.http.post("/domainNames", json=domain("admin"), headers={
        **AUTH, "RPP-Preset": "preset=org.example.rpp.preset.plain;version=2.0"})

    assert unknown.status_code == 400 and unknown.headers["RPP-Code"] == "02004"
    assert version.status_code == 400 and version.headers["RPP-Code"] == "02004"


def test_the_response_names_the_preset_applied():
    app = App()

    response = app.http.get("/presets/org.example.rpp.preset.constrained", headers=AUTH)

    assert response.headers["RPP-Preset"] == "preset=org.example.rpp.preset.plain;version=1.0"      # the default one applied
    assert response.json()["profiles"] == [{"@type": "profile", "id": ADMIN_ONLY[0], "version": "1.0"}]


def test_a_preset_with_two_bases_reads_as_the_union_and_what_two_bases_share_once():
    registry_presets = [preset("left", base_presets=[BASE["id"]], profiles=[ADMIN_ONLY[0]]),
                        preset("right", base_presets=[BASE["id"]], profiles=[ADMIN_ONLY[0], AUTH_REQUIRED[0]]),
                        preset("both", base_presets=["org.example.rpp.preset.left", "org.example.rpp.preset.right"])]
    profile = EPP_PROFILE.with_changes({"presets": ["both"], "default_preset": "both"})
    http = create_app(SessionPool(epp_backends(lambda u, p: FakeEppClient(u, p))), profile, discovery_settings=DISCOVERY,
                      registry=registry_with(registry_presets, PROFILES)).test_client()

    body = http.get("/presets/org.example.rpp.preset.both", headers=AUTH).json()
    discovery = http.get("/.well-known/rpp", headers={"Accept": MEDIA_TYPE, "RPP-Cltrid": "c"}).json()

    assert [p["id"] for p in body["profiles"]] == [ADMIN_ONLY[0], AUTH_REQUIRED[0]]
    assert [b["id"] for b in body["basePresets"]] == ["org.example.rpp.preset.left", "org.example.rpp.preset.right"]
    assert [p["id"] for p in discovery["profiles"]] == [ADMIN_ONLY[0], AUTH_REQUIRED[0]]


def test_the_profile_is_read_with_its_bases_and_required_extension_flattened():
    http = App(bound={"plain": ["at-most-one"]}).http

    body = http.get(f"/profiles/{AT_MOST_ONE[0]}", headers=AUTH).json()
    entry = http.get("/.well-known/rpp", headers={"Accept": MEDIA_TYPE, "RPP-Cltrid": "c"}).json()

    assert body["baseProfiles"] == [{"@type": "profile", "id": ADMIN_ONLY[0], "version": "1.0"}]
    plain = next(p for p in entry["presets"] if p["id"] == PLAIN[0])
    assert plain["boundProfiles"] == [{"@type": "profile", "id": AT_MOST_ONE[0], "version": "1.0"}]
    assert {AT_MOST_ONE[0], ADMIN_ONLY[0]} <= {p["id"] for p in entry["profiles"]}


@pytest.mark.parametrize("change, presets, message", [
    ({"bound_profiles": {"plain": ["admin-only", "admin-only"]}}, PRESETS, "names a profile twice"),
    ({"presets": ["plain", "nope"]}, PRESETS, "unknown preset nope"),
    ({"informational_profiles": ["nope"]}, PRESETS, "informational_profiles names an unknown profile nope"),
    ({"informational_profiles": ["admin-only", "admin-only"]}, PRESETS, "informational_profiles names a profile twice"),
    ({"informational_profiles": ["admin-only"]}, PRESETS, "informational_profiles names admin-only, which no offered preset"),
])
def test_a_configuration_the_checks_refuse_does_not_start_the_server(change, presets, message):
    profile = EPP_PROFILE.with_changes({"presets": ["plain"], "default_preset": "plain", **change})

    with pytest.raises(ValueError, match=message):
        create_app(None, profile, registry=registry_with(presets, PROFILES))


LONG_EMAIL = [{"op": "replace", "path": "/contactInfo/emails/email/address", "value": "a-long-address@example.example"}]


def test_a_patch_that_needs_no_read_is_checked_on_the_patched_contact_under_a_preset_with_a_profile():
    app = App(replies=[contact_info()])
    short = {**AUTH, "RPP-Preset": f"preset={SHORT[0]};version=1.0"}

    response = app.http.patch("/contacts/JD-1234", json=LONG_EMAIL, headers=short)

    assert response.status_code == 422 and response.headers["RPP-Code"] == "02308"
    error = response.json()["errors"][0]
    assert error["profile"] == SHORT_EMAIL[0] and error["paths"][0].startswith("$.contactInfo.emails")
    assert len(app.sent()) == 1 and "contact:info" in app.sent()[0]         # the read for it, and no update


def test_the_same_patch_under_a_preset_without_the_profile_is_sent_without_a_read():
    app = App(replies=[DONE, contact_info()])

    response = app.http.patch("/contacts/JD-1234", json=LONG_EMAIL, headers=AUTH)

    assert response.status_code == 200
    assert "contact:update" in app.sent()[0]


# A profile the server checks itself (`informational_profiles`, #232): it applies and is advertised, the proxy does not check it.

def test_a_request_that_breaks_an_informational_profile_goes_on_to_the_server():
    app = App(informational=["admin-only"])

    response = app.create(domain("billing"), "constrained")

    assert response.status_code not in (400, 422), response.text
    assert app.sent()       # the server answers what the profile forbids


def test_a_request_under_an_informational_profile_still_fails_the_preset_schema_with_400():
    app = App(informational=["admin-only"])

    response = app.create({**domain("billing"), "surprise": 1}, "constrained")

    assert response.status_code == 400 and response.headers["RPP-Code"] == "02001"
    assert app.sent() == []


def test_only_the_profile_named_is_informational_and_its_base_is_still_checked():
    app = App(bound={"plain": ["at-most-one"]}, informational=["at-most-one"])

    too_many = app.create(domain("admin", "admin"), "plain")       # at-most-one: left to the server
    wrong_label = app.create(domain("tech"), "plain")              # admin-only, its base: checked

    assert too_many.status_code not in (400, 422), too_many.text
    assert wrong_label.status_code == 422 and wrong_label.json()["errors"][0]["profile"] == ADMIN_ONLY[0]


def test_a_full_update_that_breaks_an_informational_profile_goes_on():
    app = App(replies=[info("ns1.foo.example"), DONE, info("ns1.foo.example", "ns2.foo.example")], informational=["one-nameserver"])

    response = app.http.put("/domainNames/foo.example", json={"@type": "domainName", "nameservers": TWO},
                            headers=LIMITED_HEADERS)

    assert response.status_code == 200, response.text


def test_a_patch_under_an_informational_profile_is_sent_as_an_update_without_a_read():
    app = App(replies=[DONE, info("ns1.foo.example", "ns2.foo.example")], informational=["one-nameserver"])
    add = [{"op": "add", "path": "/nameservers", "value": TWO[1]}]

    response = app.http.patch("/domainNames/foo.example", json=add, headers=LIMITED_HEADERS)

    assert response.status_code == 200, response.text
    assert "domain:update" in app.sent()[0]          # no read before it: the server decides


def test_a_contact_patch_under_an_informational_profile_is_sent_without_a_read():
    app = App(replies=[DONE, contact_info()], informational=["short-email"])
    short = {**AUTH, "RPP-Preset": f"preset={SHORT[0]};version=1.0"}

    response = app.http.patch("/contacts/JD-1234", json=LONG_EMAIL, headers=short)

    assert response.status_code == 200, response.text
    assert "contact:update" in app.sent()[0]


def test_an_informational_profile_is_advertised_as_one_the_proxy_checks():
    checked = App().http
    informational = App(informational=["admin-only"]).http
    discovery = {"Accept": MEDIA_TYPE, "RPP-Cltrid": "c"}
    path = f"/presets/{CONSTRAINED[0]}"

    for http in (checked, informational):
        assert http.get(path, headers=AUTH).json()["profiles"] == [{"@type": "profile", "id": ADMIN_ONLY[0], "version": "1.0"}]
        assert ADMIN_ONLY[0] in {p["id"] for p in http.get("/.well-known/rpp", headers=discovery).json()["profiles"]}
    schema = {"Accept": "application/schema+json", "RPP-Cltrid": "c"}
    assert checked.get(path + "/schema", headers=schema).json() == informational.get(path + "/schema", headers=schema).json()
