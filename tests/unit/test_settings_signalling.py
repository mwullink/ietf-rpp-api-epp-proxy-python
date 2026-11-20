import pytest

from settings.load_settings import load_settings


def write(tmp_path, extra=""):
    path = tmp_path / "c.yaml"
    path.write_text("rpp_epp_host: h\n" + extra)
    return str(path)


@pytest.mark.pyversions
def test_the_signalling_is_the_header_without_the_key(tmp_path):
    assert load_settings(write(tmp_path)).preset_signalling == "header"


def test_the_header_can_be_named(tmp_path):
    assert load_settings(write(tmp_path, "rpp_preset_signalling: header\n")).preset_signalling == "header"


def test_the_media_type_can_be_named(tmp_path):
    assert load_settings(write(tmp_path, "rpp_preset_signalling: media-type\n")).preset_signalling == "media-type"


def test_an_unknown_method_stops_the_server(tmp_path):
    with pytest.raises(ValueError, match="rpp_preset_signalling"):
        load_settings(write(tmp_path, "rpp_preset_signalling: cookie\n"))


@pytest.mark.parametrize("config, method", [("config.yaml", "header"), ("config.rri-mtest.yaml", "media-type")])
def test_the_configs_of_the_test_environments_use_both_methods(config, method):
    assert load_settings(config).preset_signalling == method
