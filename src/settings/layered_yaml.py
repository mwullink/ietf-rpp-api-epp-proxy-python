"""A YAML mapping composed of layers (#217): the app configuration and the test environment descriptors.

A file may start with `include: [<path>, ...]`, paths relative to that file. A file F resolves to its includes, in
order and each resolved the same way, then F itself, then the untracked `F.local.yaml` next to it if there is one
(`<stem>.local.yaml`), so every layer can be changed on one machine. A later layer merges into an earlier one: a
mapping merges key by key, any other value (a list, a scalar, null) replaces. A file that is included twice, along two
paths, is applied twice, which changes nothing.
"""
from dataclasses import dataclass, field
from pathlib import Path

import yaml

INCLUDE = "include"
LOCAL_SUFFIX = ".local.yaml"


class LayerError(ValueError):
    """A layer is missing, includes itself, or is not a mapping."""


@dataclass
class Layered:
    """The merged mapping, and for each top-level key the file of the layer that set it last."""
    data: dict = field(default_factory=dict)
    sources: dict[str, Path] = field(default_factory=dict)


def local_path(path: Path) -> Path:
    """The untracked override of `path`: config/environments/rri-mtest.yaml → rri-mtest.local.yaml."""
    return path.with_name(path.stem + LOCAL_SUFFIX)


def is_local(path: Path) -> bool:
    return path.name.endswith(LOCAL_SUFFIX)


def load_layered(path: str | Path) -> Layered:
    """The mapping `path` resolves to, with its includes and the local files of every layer."""
    result = Layered()
    _apply_file(Path(path).resolve(), result, ())
    return result


def _apply_file(path: Path, result: Layered, chain: tuple[Path, ...]) -> None:
    if path in chain:
        raise LayerError("include cycle: " + " → ".join(str(p) for p in (*chain, path)))
    data = _read(path, chain)
    includes = data.pop(INCLUDE, None) or []
    if isinstance(includes, str):
        includes = [includes]
    if not isinstance(includes, list) or not all(isinstance(include, str) and include for include in includes):
        raise LayerError(f"{path}: `{INCLUDE}` is a list of paths")
    for include in includes:
        _apply_file((path.parent / include).resolve(), result, (*chain, path))
    _apply(data, path, result)
    local = local_path(path)
    if not is_local(path) and local.exists():
        local_data = _read(local, chain)
        if INCLUDE in local_data:
            raise LayerError(f"{local}: a local file includes nothing")
        _apply(local_data, local, result)


def _read(path: Path, chain: tuple[Path, ...]) -> dict:
    if not path.exists():
        named_by = f" (included by {chain[-1]})" if chain else ""
        raise LayerError(f"{path}: no such file{named_by}")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise LayerError(f"{path}: not a mapping")
    return data


def _apply(data: dict, path: Path, result: Layered) -> None:
    for key, value in data.items():
        result.data[key] = merge(result.data.get(key), value)
        result.sources[key] = path


def merge(base, layer):
    """`layer` over `base`: two mappings merge key by key, otherwise `layer` replaces."""
    if isinstance(base, dict) and isinstance(layer, dict):
        merged = dict(base)
        for key, value in layer.items():
            merged[key] = merge(base.get(key), value)
        return merged
    return layer
