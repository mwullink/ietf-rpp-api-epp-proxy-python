"""#207: the configuration templates of the example Ansible inventory (deploy/ansible/inventory/example/configs), rendered
with the instances of its group_vars, are configurations the proxy starts with. Each is made from a configuration of the
repository, which its header names: it states no key that one lacks, with its includes (#217) (a key the proxy does not know is ignored, so a
renamed key would go unnoticed), and the same signalling and backend profile."""
import dataclasses
import json
import re
from urllib.parse import urlsplit

import jinja2
import pytest
import yaml
from starlette.testclient import TestClient

from main import compose
from settings.layered_yaml import load_layered
from settings.load_settings import load_settings
from settings.sqlite_settings import SqliteSettings
from tests.helper.test_environment import REPOSITORY

INVENTORY = REPOSITORY / "deploy" / "ansible" / "inventory" / "example"
MADE_FROM = re.compile(r"made from (config/environments/[\w.-]+\.yaml) of the repository")


def instances() -> list[dict]:
    group_vars = yaml.safe_load((INVENTORY / "group_vars" / "rpp_hosts" / "main.yml").read_text())
    return group_vars["rpp_proxy_instances"]


def render(instance: dict) -> str:
    env = jinja2.Environment(undefined=jinja2.StrictUndefined, keep_trailing_newline=True)
    env.filters["to_json"] = json.dumps
    env.filters["urlsplit"] = lambda url, part: getattr(urlsplit(url), part)
    template = env.from_string((INVENTORY / instance["config_template"]).read_text())
    # The vault's clients: the demo hashes of the repository, which the vault never holds.
    demo_clients = load_layered(REPOSITORY / "config/environments/sqlite-demo.yaml").data["rpp_sqlite_clients"]
    return template.render(ansible_managed="Ansible managed", instance={**instance, "sqlite_clients": demo_clients})


@pytest.fixture(params=instances(), ids=lambda instance: instance["name"])
def rendered(request, tmp_path):
    text = render(request.param)
    path = tmp_path / f"{request.param['name']}.yaml"
    path.write_text(text)
    source = MADE_FROM.search(text)
    assert source, f"{request.param['config_template']} names no configuration of the repository it is made from"
    return path, REPOSITORY / source.group(1)


def test_a_template_states_no_key_its_repository_configuration_lacks(rendered):
    path, source = rendered

    assert set(yaml.safe_load(path.read_text())) - set(load_layered(source).data) == set()


def test_a_template_has_the_signalling_and_the_profile_of_its_repository_configuration(rendered):
    path, source = rendered
    settings, repository = load_settings(str(path)), load_settings(str(source))

    assert settings.backend == repository.backend
    assert settings.preset_signalling == repository.preset_signalling
    assert settings.profile_layers == repository.profile_layers
    assert settings.extensions == repository.extensions


def test_the_proxy_starts_with_a_template(rendered, tmp_path):
    path, _ = rendered
    settings = load_settings(str(path))
    if settings.backend == "sqlite":
        settings = dataclasses.replace(settings, sqlite=SqliteSettings(
            rpp_sqlite_url=f"sqlite:///{tmp_path / 'demo.db'}", rpp_sqlite_clients=settings.sqlite.rpp_sqlite_clients))

    composition = compose(settings)
    try:
        response = TestClient(composition.app).get("/.well-known/rpp", headers={"RPP-Cltrid": "deploy-1"})
        assert response.status_code == 200
    finally:
        composition.sessions.close()
