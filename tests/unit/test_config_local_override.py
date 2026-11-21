import pytest

from settings.load_settings import load_settings


def load(tmp_path, monkeypatch, base, local=None, name="config.yaml"):
    (tmp_path / name).write_text(base)
    if local is not None:
        (tmp_path / name.replace(".yaml", ".local.yaml")).write_text(local)
    monkeypatch.setenv("RPP_CONFIG_FILE", str(tmp_path / name))
    return load_settings()


def test_without_a_local_file_the_base_file_is_used(tmp_path, monkeypatch):
    settings = load(tmp_path, monkeypatch, "rpp_epp_host: base.example\nrpp_epp_port: 743\n")

    assert settings.epp.rpp_epp_host == "base.example"
    assert settings.epp.rpp_epp_port == 743


def test_the_local_file_replaces_the_keys_it_has(tmp_path, monkeypatch):
    settings = load(tmp_path, monkeypatch, "rpp_epp_host: base.example\nrpp_epp_port: 743\n",
                    "rpp_epp_host: local.example\n")

    assert settings.epp.rpp_epp_host == "local.example"
    assert settings.epp.rpp_epp_port == 743


def test_the_local_file_merges_into_a_mapping(tmp_path, monkeypatch):
    settings = load(tmp_path, monkeypatch, "rpp_epp_host: h\nrpp_idn_lgr_tables:\n  latn-1.0: de\n  spa-1.0: es\n",
                    "rpp_idn_lgr_tables:\n  latn-1.0: xx\n")

    assert settings.epp.rpp_idn_lgr_tables == {"latn-1.0": "xx", "spa-1.0": "es"}


def test_the_local_file_unsets_a_key_with_null(tmp_path, monkeypatch):
    settings = load(tmp_path, monkeypatch, "rpp_epp_host: h\nrpp_epp_port: 7043\n", "rpp_epp_port: null\n")

    assert settings.epp.rpp_epp_port == 700


def test_an_unknown_key_of_the_proxy_is_named_with_its_file(tmp_path, monkeypatch, caplog):
    load(tmp_path, monkeypatch, "rpp_epp_host: h\nother: 1\n", "rpp_epp_hots: typo\n")

    warnings = [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]
    assert warnings == [f"Unknown configuration key rpp_epp_hots in {tmp_path / 'config.local.yaml'}: ignored"]


def test_a_known_key_is_not_warned_about(tmp_path, monkeypatch, caplog):
    load(tmp_path, monkeypatch, "rpp_backend: rri\nrpp_rri_host: h\nrpp_backend_profile:\n  extends: rri\n"
                                "rpp_preset_signalling: header\nrpp_extensions: []\nrpp_tlds: [de]\n")

    assert [r for r in caplog.records if r.levelname == "WARNING"] == []


def test_without_a_file_named_the_default_is_the_epp_test_environment(monkeypatch):
    from settings.load_settings import DEFAULT_CONFIG
    monkeypatch.delenv("RPP_CONFIG_FILE", raising=False)

    assert DEFAULT_CONFIG.relative_to(DEFAULT_CONFIG.parents[2]).as_posix() == "config/environments/epp-docker.yaml"
    assert load_settings().epp.rpp_epp_host == load_settings(str(DEFAULT_CONFIG)).epp.rpp_epp_host


def test_an_empty_local_file_changes_nothing(tmp_path, monkeypatch):
    settings = load(tmp_path, monkeypatch, "rpp_epp_host: base.example\n", "")

    assert settings.epp.rpp_epp_host == "base.example"


def test_the_local_file_sits_next_to_the_file_named_by_the_environment(tmp_path, monkeypatch):
    settings = load(tmp_path, monkeypatch, "rpp_epp_host: base.example\n", "rpp_epp_host: local.example\n",
                    name="other.yaml")

    assert settings.epp.rpp_epp_host == "local.example"


def test_the_profile_is_the_protocols_without_a_profile_of_the_server(tmp_path, monkeypatch):
    settings = load(tmp_path, monkeypatch, "rpp_backend: rri\n")

    generic, specific = settings.profile_layers
    assert generic["name"] == "RRI"
    assert specific == {}


def test_the_profile_of_the_server_extends_a_generic_one(tmp_path, monkeypatch):
    settings = load(tmp_path, monkeypatch,
                    "rpp_backend_profile:\n  extends: epp\n  contact:\n    fax:\n      supported: false\n")

    generic, specific = settings.profile_layers
    assert generic["name"] == "EPP"
    assert specific == {"contact": {"fax": {"supported": False}}}


def test_a_profile_extends_only_a_generic_one(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="extends one of epp, rri"):
        load(tmp_path, monkeypatch, "rpp_backend_profile:\n  extends: ../secrets\n")


def test_the_lgrs_come_from_the_config_of_the_protocol(tmp_path, monkeypatch):
    assert load(tmp_path, monkeypatch, "rpp_idn_lgr_tables:\n  latn-1.0: de\n").lgrs == ("latn-1.0",)
    assert load(tmp_path, monkeypatch, "rpp_backend: rri\nrpp_rri_lgr: latn-1.0\n").lgrs == ("latn-1.0",)
    assert load(tmp_path, monkeypatch, "rpp_backend: rri\n").lgrs == ()
