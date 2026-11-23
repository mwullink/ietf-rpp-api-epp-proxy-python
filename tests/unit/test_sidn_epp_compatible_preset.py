"""The SIDN EPP compatible preset: the EPP compatible preset for the SIDN EPP server, which holds no <contact:authInfo> (RFC 5733
§3.2.1 requires one in a create) and only the localized postal info of a contact (<contact:postalInfo type="loc">). Its profile is
the EPP Compatibility Profile without that requirement, without the authInfo of a contact, and with the name, the organisations and
the addresses of a contact in the one localization of its Card alone; a preset is a union and cannot take a constraint of another
away, so it is built on the base preset."""
import copy
from urllib.parse import quote

import pytest

from core.session.session_pool import SessionPool
from rpp.http.app import create_app
from rpp.schema.definitions import Definitions
from rpp.schema.extensions import EXTENSIONS
from rpp.schema.offered_presets import OfferedPresets
from tests.helper.epp_backends import epp_backends
from tests.helper.fake_epp_client import FakeEppClient
from tests.helper.presets import EPP, EPP_COMPATIBILITY
from tests.helper.profiles import EPP_PROFILE
from tests.unit.test_contact_put_wire import AUTH, CONTACT_NS, epp_reply
from tests.unit.test_preset_schemas import schema_of, validator_of
from tests.unit.test_rri_wire import DISCOVERY, HEADERS

SIDN = "nl.sidn.rpp.preset.epp-compatible"
SIDN_PROFILE = "nl.sidn.rpp.profile.epp-compatibility"
KEYS = ["base", "epp-compatible", "sidn-epp-compatible"]

PROFILE = EPP_PROFILE.with_changes({"presets": KEYS, "default_preset": "sidn-epp-compatible", "contact.authInfo.supported": False})

ADDRESS = {"addr": {"components": [{"kind": "name", "value": "Hauptstraße 1"}, {"kind": "locality", "value": "München"}], "countryCode": "DE"}}
EMAILS = {"email": {"address": "jdoe@example.example"}}

# What the SIDN profile asks of a Card: the localization alone holds the name, the organisations and the addresses.
LOC_CARD = {"@type": "Card", "version": "2.0", "emails": EMAILS,
            "localizations": {"und": {"name": {"full": "Jörg Müller"}, "addresses": ADDRESS}}}
# What the EPP Compatibility Profile asks of a Card: the Card itself holds them, in US-ASCII.
INT_CARD = {"@type": "Card", "version": "2.0", "name": {"full": "John Doe"}, "emails": EMAILS,
            "addresses": {"addr": {"components": [{"kind": "locality", "value": "Arnhem"}], "countryCode": "NL"}}}
AUTH_INFO = {"@type": "authInfo", "method": "authinfo", "authdata": "Abc2345678"}


def client():
    sessions = SessionPool(epp_backends(lambda username, password: FakeEppClient(username, password)))
    return create_app(sessions, PROFILE, discovery_settings=DISCOVERY).test_client()


def contact(card=LOC_CARD, **members):
    return {"@type": "contact", "id": "C1", "contactInfo": card, **members}


def with_card(**members):
    card = copy.deepcopy(LOC_CARD)
    card.update(members)
    return card


def with_localization(**members):
    card = copy.deepcopy(LOC_CARD)
    card["localizations"]["und"].update(members)
    return card


def without_localization(*names):
    card = copy.deepcopy(LOC_CARD)
    for name in names:
        del card["localizations"]["und"][name]
    return card


def sidn(definition="contact.create"):
    return validator_of(schema_of(client(), SIDN), definition)


def test_the_preset_is_built_on_the_base_preset_and_applies_the_sidn_profile_alone():
    presets = OfferedPresets.build(Definitions.load(None, EXTENSIONS), KEYS, "sidn-epp-compatible", {}, ())

    preset = next(item for item in presets.offered if item.id == SIDN)
    assert [item.id for item in preset.profiles] == [SIDN_PROFILE]
    assert preset.extensions == () and presets.default is preset


def test_the_preset_and_its_profile_are_read_and_the_other_presets_are_unchanged():
    http = client()

    preset = http.get(f"/presets/{quote(SIDN, safe='')}", headers=HEADERS)
    profile = http.get(f"/profiles/{quote(SIDN_PROFILE, safe='')}", headers=HEADERS)
    epp = http.get(f"/presets/{quote(EPP, safe='')}", headers=HEADERS)

    assert preset.status_code == 200 and preset.json()["profiles"] == [{"@type": "profile", "id": SIDN_PROFILE, "version": "1.0"}]
    assert preset.json()["defaultPreset"] is True
    assert profile.status_code == 200 and profile.json()["id"] == SIDN_PROFILE
    assert epp.json()["profiles"] == [{"@type": "profile", "id": EPP_COMPATIBILITY, "version": "1.0"}]


def test_a_contact_is_created_without_authInfo_under_the_sidn_preset_and_not_under_the_epp_compatible_one():
    epp = validator_of(schema_of(client(), EPP), "contact.create")

    assert sidn().is_valid(contact())
    assert not epp.is_valid(contact(INT_CARD))      # RFC 5733: the profile requires an authInfo
    assert epp.is_valid(contact(INT_CARD, authInfo=AUTH_INFO))


def test_a_contact_has_no_authInfo_under_the_sidn_preset():
    for definition in ("contact.create", "contact.read", "contact.update"):
        body = {"@type": "contact", "contactInfo": LOC_CARD, "authInfo": AUTH_INFO}
        if definition != "contact.update":
            body["id"] = "C1"
        if definition == "contact.read":
            body |= {"provMetadata": {"@type": "provMetadata", "spClientId": "REG", "repositoryId": "R"}, "status": [{"@type": "contactStatus", "label": "ok"}]}

        assert not sidn(definition).is_valid(body), definition


def test_only_the_localization_of_the_card_holds_the_name_the_organisations_and_the_addresses():
    assert sidn().is_valid(contact())
    assert sidn().is_valid(contact(with_localization(organizations={"org": {"name": "Müller GmbH"}})))      # not US-ASCII
    for members in ({"name": {"full": "John Doe"}},
                    {"organizations": {"org": {"name": "Example Inc."}}},
                    {"addresses": INT_CARD["addresses"]}):
        assert not sidn().is_valid(contact(with_card(**members))), members


def test_the_localization_is_required_and_is_one_with_a_name_and_an_address():
    assert not sidn().is_valid(contact({key: value for key, value in INT_CARD.items()}))      # an int-only Card
    assert not sidn().is_valid(contact({key: value for key, value in LOC_CARD.items() if key != "localizations"}))
    assert not sidn().is_valid(contact(with_card(localizations={})))
    assert not sidn().is_valid(contact(with_card(localizations={**LOC_CARD["localizations"], "de": LOC_CARD["localizations"]["und"]})))
    assert not sidn().is_valid(contact(without_localization("name")))
    assert not sidn().is_valid(contact(without_localization("addresses")))
    assert not sidn().is_valid(contact(with_localization(emails={"email": {"address": "x@example.example"}})))


def test_the_rest_of_the_epp_compatibility_profile_still_applies():
    assert not sidn().is_valid(contact({key: value for key, value in LOC_CARD.items() if key != "emails"}))
    assert not sidn().is_valid(contact(with_card(emails={"email": {"address": "jörg@example.example"}})))      # US-ASCII
    assert not sidn().is_valid(contact(with_card(phones={"mobile": {"number": "tel:+49.1234"}})))
    no_locality = copy.deepcopy(ADDRESS)
    no_locality["addr"]["components"] = [{"kind": "name", "value": "Hauptstraße 1"}]
    assert not sidn().is_valid(contact(with_localization(addresses=no_locality)))
    no_country = {"addr": {"components": ADDRESS["addr"]["components"]}}
    assert not sidn().is_valid(contact(with_localization(addresses=no_country)))


def test_a_loc_only_contact_is_read_under_the_sidn_preset_and_an_int_one_is_not():
    read = {"@type": "contact", "id": "C1", "status": [{"@type": "contactStatus", "label": "ok"}],
            "provMetadata": {"@type": "provMetadata", "spClientId": "REG", "repositoryId": "R"}}

    assert sidn("contact.read").is_valid({**read, "contactInfo": LOC_CARD})
    assert not sidn("contact.read").is_valid({**read, "contactInfo": INT_CARD})


def test_a_domain_still_has_its_authInfo_under_the_sidn_preset():
    assert sidn("domainName.create").is_valid({"@type": "domainName", "name": "example.example", "authInfo": AUTH_INFO})


CREATED = (True, "1000", epp_reply(1000, (
    f'<resData><contact:creData {CONTACT_NS}><contact:id>JD-1234</contact:id>'
    '<contact:crDate>2026-11-04T10:00:00.0Z</contact:crDate></contact:creData></resData>')))

LOC_INFO = (True, "1000", epp_reply(1000, (
    f'<resData><contact:infData {CONTACT_NS}><contact:id>JD-1234</contact:id><contact:roid>C1</contact:roid>'
    '<contact:status s="ok"/><contact:postalInfo type="loc"><contact:name>Jörg Müller</contact:name>'
    '<contact:addr><contact:street>Hauptstraße 1</contact:street><contact:city>München</contact:city>'
    '<contact:cc>DE</contact:cc></contact:addr></contact:postalInfo>'
    '<contact:email>jdoe@example.example</contact:email><contact:clID>user</contact:clID><contact:crID>user</contact:crID>'
    '<contact:crDate>2026-11-04T10:00:00.0Z</contact:crDate></contact:infData></resData>')))


@pytest.fixture
def created():
    """POST /contacts of a Card with its localization alone, under the default preset (the SIDN one), and the EPP client."""
    holder = {}

    def factory(username, password):
        holder["client"] = FakeEppClient(username, password, replies=[CREATED, LOC_INFO])
        return holder["client"]

    http = create_app(SessionPool(epp_backends(factory)), PROFILE, discovery_settings=DISCOVERY).test_client()
    body = {"@type": "contact", "id": "JD-1234", "contactInfo": LOC_CARD}
    return http.post("/contacts", headers=AUTH, json=body), holder["client"]


def test_the_proxy_sends_the_localization_as_the_only_postal_info_of_the_create(created):
    response, epp = created

    assert response.status_code == 201, response.text
    assert 'type="loc"' in epp.sent[0] and 'type="int"' not in epp.sent[0]
    assert "Jörg Müller" in epp.sent[0] and "München" in epp.sent[0]


def test_the_proxy_reads_a_contact_with_only_a_loc_postal_info_as_a_localization(created):
    response, _ = created

    card = response.json()["contactInfo"]
    assert response.headers["RPP-Code"] == "01000"
    assert not {"name", "organizations", "addresses"} & set(card)
    assert card["localizations"]["und"]["name"] == {"full": "Jörg Müller"}
    assert card["localizations"]["und"]["addresses"]["addr"]["countryCode"] == "DE"


def test_the_proxy_refuses_a_create_with_the_int_form_of_the_card_under_the_sidn_preset():
    sessions = SessionPool(epp_backends(lambda username, password: FakeEppClient(username, password)))
    http = create_app(sessions, PROFILE, discovery_settings=DISCOVERY).test_client()

    response = http.post("/contacts", headers=AUTH, json=contact(INT_CARD) | {"id": "JD-1234"})

    assert response.status_code == 422 and response.headers["RPP-Code"] == "02308"
    assert response.json()["errors"][0]["profile"] == SIDN_PROFILE
