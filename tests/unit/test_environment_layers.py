"""#217: the test environment descriptors are layered like the configurations, each with an untracked `.local.yaml`."""
import pytest

from tests.helper import test_environment
from tests.helper.test_environment import EnvironmentError, _descriptor, config_file, environment_names


@pytest.fixture
def environments(tmp_path, monkeypatch):
    directory = tmp_path / "tests" / "integration" / "environments"
    (directory / "common").mkdir(parents=True)
    monkeypatch.setattr(test_environment, "REPOSITORY", tmp_path)
    monkeypatch.setattr(test_environment, "ENVIRONMENTS", directory)
    monkeypatch.setattr(test_environment, "CONFIGS", tmp_path / "config" / "environments")
    return directory


def test_the_names_are_the_descriptors_not_their_local_files_or_common_layers(environments):
    for name in ("a.yaml", "a.local.yaml", "b.yaml", "common/shared.yaml"):
        (environments / name).write_text("{}\n")

    assert environment_names() == ["a", "b"]


def test_a_local_file_is_no_environment(environments):
    (environments / "a.yaml").write_text("{}\n")
    (environments / "a.local.yaml").write_text("{}\n")

    with pytest.raises(EnvironmentError, match="No test environment 'a.local'"):
        _descriptor("a.local")


def test_the_config_is_the_one_of_the_same_name_unless_stated(environments, tmp_path):
    (environments / "a.yaml").write_text("max_workers: 2\n")
    (environments / "b.yaml").write_text("config: config/environments/a.yaml\n")

    assert _descriptor("a")["config"] == "config/environments/a.yaml"
    assert config_file("a") == str(tmp_path / "config" / "environments" / "a.yaml")
    assert _descriptor("b")["config"] == "config/environments/a.yaml"


def test_a_descriptor_merges_its_common_layer_and_its_local_file(environments):
    (environments / "common" / "shared.yaml").write_text(
        "max_workers: 4\nfacts:\n  a:\n    x: 1\n    y: 1\n  b: [1, 2]\n")
    (environments / "e.yaml").write_text("include: [common/shared.yaml]\nfacts:\n  a:\n    y: null\n")
    (environments / "e.local.yaml").write_text("max_workers: 1\nfacts:\n  b: [3]\n")

    data = _descriptor("e")

    assert data["max_workers"] == 1
    assert data["facts"] == {"a": {"x": 1, "y": None}, "b": [3]}


def test_a_broken_layer_names_the_environment(environments):
    (environments / "e.yaml").write_text("include: [common/gone.yaml]\n")

    with pytest.raises(EnvironmentError, match="Test environment 'e': .*gone.yaml: no such file"):
        _descriptor("e")


def test_the_server_is_the_environment_unless_its_descriptor_names_one():
    """#232: epp-docker-checked runs over the server of epp-docker, and the SQLite demos each over their own."""
    assert test_environment.load("epp-docker", with_credentials=False).server == "epp-docker"
    assert test_environment.load("epp-docker-checked", with_credentials=False).server == "epp-docker"
    assert test_environment.load("sqlite-demo-bound", with_credentials=False).server == "sqlite-demo-bound"


def test_epp_docker_checked_is_epp_docker_with_the_profile_checked_by_the_proxy():
    informational = test_environment.load("epp-docker", with_credentials=False)
    checked = test_environment.load("epp-docker-checked", with_credentials=False)

    assert informational.profile.informational_profiles == ("epp-compatibility",)
    assert checked.profile.informational_profiles == ()
    assert checked.facts == informational.facts
