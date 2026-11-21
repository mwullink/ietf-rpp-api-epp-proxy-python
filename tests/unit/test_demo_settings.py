"""The settings of the extensions and of the SQLite backend."""
import dataclasses

import pytest

from main import compose
from settings.load_settings import load_settings
from settings.sqlite_settings import SqliteSettings
from tests.helper.test_environment import REPOSITORY


def write(tmp_path, text):
    path = tmp_path / "config.yaml"
    path.write_text(text)
    return str(path)


def test_the_demo_configuration_names_the_backend_the_clients_and_the_extension():
    settings = load_settings(str(REPOSITORY / "config/environments/sqlite-demo.yaml"))

    assert settings.backend == "sqlite"
    assert settings.extensions == ("extensions.planets",)
    assert sorted(settings.sqlite.rpp_sqlite_clients) == ["demo-a", "demo-b", "demo-c", "demo-d"]
    assert settings.sqlite.rpp_sqlite_url == "sqlite://"
    assert settings.lgrs == ()


def test_without_extensions_none_are_registered(tmp_path):
    assert load_settings(write(tmp_path, "rpp_backend: sqlite\n")).extensions == ()


@pytest.mark.parametrize("value", ["extensions.planets", "[1]", "[a, a]", "['']"])
def test_rpp_extensions_is_a_list_of_distinct_module_paths(tmp_path, value):
    with pytest.raises(ValueError, match="rpp_extensions"):
        load_settings(write(tmp_path, f"rpp_backend: sqlite\nrpp_extensions: {value}\n"))


@pytest.mark.parametrize("clients", [["a"], {"a": ""}, {"": "x"}, {"a": 1}])
def test_the_clients_map_each_user_to_a_hash(clients):
    with pytest.raises(ValueError, match="rpp_sqlite_clients"):
        SqliteSettings(rpp_sqlite_clients=clients)


def test_the_hashes_are_not_in_the_repr_of_the_settings():
    settings = SqliteSettings(rpp_sqlite_clients={"a": "scrypt$secret"})

    assert "secret" not in repr(settings)


def test_an_unusable_client_hash_stops_the_app_without_naming_the_hash():
    settings = load_settings(str(REPOSITORY / "config/environments/sqlite-demo.yaml"))
    bad = dataclasses.replace(settings, sqlite=SqliteSettings(rpp_sqlite_clients={"demo-a": "scrypt$3$8$1$AA==$AA=="}))

    with pytest.raises(ValueError, match="rpp_sqlite_clients: the hash of the client 'demo-a'") as refused:
        compose(bad)
    assert "AA==" not in str(refused.value)
