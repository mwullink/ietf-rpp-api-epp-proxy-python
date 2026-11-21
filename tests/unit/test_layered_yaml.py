"""#217: a configuration composed of layers, each with an untracked `.local.yaml` (settings/layered_yaml.py)."""
import pytest

from settings.layered_yaml import LayerError, load_layered, merge


def write(directory, name, text):
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_a_file_without_includes_is_its_mapping(tmp_path):
    layered = load_layered(write(tmp_path, "a.yaml", "x: 1\ny: [1, 2]\n"))

    assert layered.data == {"x": 1, "y": [1, 2]}
    assert layered.sources == {"x": tmp_path / "a.yaml", "y": tmp_path / "a.yaml"}


def test_an_empty_file_is_an_empty_mapping(tmp_path):
    assert load_layered(write(tmp_path, "a.yaml", "")).data == {}


def test_includes_apply_in_order_then_the_file(tmp_path):
    write(tmp_path, "base/one.yaml", "x: 1\ny: 1\nz: 1\n")
    write(tmp_path, "base/two.yaml", "y: 2\nz: 2\n")
    top = write(tmp_path, "env/top.yaml", "include: [../base/one.yaml, ../base/two.yaml]\nz: 3\n")

    layered = load_layered(top)

    assert layered.data == {"x": 1, "y": 2, "z": 3}
    assert layered.sources == {"x": tmp_path / "base/one.yaml", "y": tmp_path / "base/two.yaml", "z": top}


def test_an_include_is_relative_to_the_file_that_names_it(tmp_path):
    write(tmp_path, "protocols/p.yaml", "p: 1\n")
    write(tmp_path, "backends/b.yaml", "include: [../protocols/p.yaml]\nb: 1\n")
    top = write(tmp_path, "environments/e.yaml", "include: ../backends/b.yaml\ne: 1\n")

    assert load_layered(top).data == {"p": 1, "b": 1, "e": 1}


def test_mappings_merge_and_lists_and_values_replace(tmp_path):
    write(tmp_path, "base.yaml", "m:\n  a: 1\n  n:\n    b: 1\n    c: 1\n  l: [1, 2]\n")
    top = write(tmp_path, "top.yaml", "include: [base.yaml]\nm:\n  n:\n    c: 2\n  l: [3]\n")

    assert load_layered(top).data == {"m": {"a": 1, "n": {"b": 1, "c": 2}, "l": [3]}}


def test_null_replaces_like_any_value(tmp_path):
    write(tmp_path, "base.yaml", "m:\n  a: 1\n  b: 1\n")
    top = write(tmp_path, "top.yaml", "include: [base.yaml]\nm:\n  a: null\n")

    assert load_layered(top).data == {"m": {"a": None, "b": 1}}


def test_the_local_file_of_a_layer_applies_right_after_it(tmp_path):
    write(tmp_path, "base.yaml", "x: base\ny: base\nm:\n  a: 1\n")
    write(tmp_path, "base.local.yaml", "x: base-local\nm:\n  b: 2\n")
    top = write(tmp_path, "top.yaml", "include: [base.yaml]\ny: top\n")
    write(tmp_path, "top.local.yaml", "y: top-local\n")

    layered = load_layered(top)

    assert layered.data == {"x": "base-local", "y": "top-local", "m": {"a": 1, "b": 2}}
    assert layered.sources["x"] == tmp_path / "base.local.yaml"
    assert layered.sources["y"] == tmp_path / "top.local.yaml"


def test_a_layer_overrides_the_local_file_of_the_layer_it_includes(tmp_path):
    write(tmp_path, "base.yaml", "x: base\n")
    write(tmp_path, "base.local.yaml", "x: base-local\n")
    top = write(tmp_path, "top.yaml", "include: [base.yaml]\nx: top\n")

    assert load_layered(top).data == {"x": "top"}


def test_a_local_file_includes_nothing(tmp_path):
    top = write(tmp_path, "top.yaml", "x: 1\n")
    write(tmp_path, "other.yaml", "y: 1\n")
    write(tmp_path, "top.local.yaml", "include: [other.yaml]\n")

    with pytest.raises(LayerError, match="a local file includes nothing"):
        load_layered(top)


def test_a_missing_include_names_the_file_that_names_it(tmp_path):
    write(tmp_path, "top.yaml", "include: [gone.yaml]\n")

    with pytest.raises(LayerError, match=r"gone\.yaml: no such file \(included by .*top\.yaml\)"):
        load_layered(tmp_path / "top.yaml")


def test_a_missing_file_is_an_error(tmp_path):
    with pytest.raises(LayerError, match="no such file"):
        load_layered(tmp_path / "gone.yaml")


def test_an_include_cycle_is_an_error(tmp_path):
    write(tmp_path, "a.yaml", "include: [b.yaml]\n")
    write(tmp_path, "b.yaml", "include: [a.yaml]\n")

    with pytest.raises(LayerError, match="include cycle"):
        load_layered(tmp_path / "a.yaml")


def test_a_file_included_along_two_paths_is_no_cycle(tmp_path):
    write(tmp_path, "common.yaml", "c: 1\n")
    write(tmp_path, "a.yaml", "include: [common.yaml]\na: 1\n")
    write(tmp_path, "b.yaml", "include: [common.yaml]\nb: 1\n")
    top = write(tmp_path, "top.yaml", "include: [a.yaml, b.yaml]\n")

    assert load_layered(top).data == {"c": 1, "a": 1, "b": 1}


@pytest.mark.parametrize("text, message", [("- 1\n", "not a mapping"), ("include: 3\n", "is a list of paths"),
                                           ("include: ['']\n", "is a list of paths")])
def test_a_malformed_layer_is_an_error(tmp_path, text, message):
    with pytest.raises(LayerError, match=message):
        load_layered(write(tmp_path, "a.yaml", text))


def test_merge_does_not_change_its_arguments():
    base, layer = {"m": {"a": 1}}, {"m": {"b": 2}}

    assert merge(base, layer) == {"m": {"a": 1, "b": 2}}
    assert base == {"m": {"a": 1}} and layer == {"m": {"b": 2}}
