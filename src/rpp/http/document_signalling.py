"""How an OpenAPI document of one preset states that preset (#205), so that a client reading it, or a UI, sends it: the parts of
the document the signalling methods change. The methods themselves (`HeaderPresetSignalling`, `MediaTypePresetSignalling`) decide
what to write; this module only finds and rewrites the places in the document."""
from rpp.http.headers import RPP_MEDIA_TYPE
from rpp.http.preset_header import HEADER as PRESET_HEADER
from rpp.http.served_document import METHODS

_COMPONENT_PARAMETERS = "#/components/parameters/"
CONTENT_TYPE_PARAMETER = "rpp.PresetContentType"


def _operations(document: dict):
    for item in document.get("paths", {}).values():
        for method in METHODS:
            if isinstance(item.get(method), dict):
                yield item[method]


def _is_preset_parameter(parameter: dict) -> bool:
    return parameter.get("in") == "header" and str(parameter.get("name", "")).lower() == PRESET_HEADER.lower()


def preset_parameters(document: dict):
    """The parameter objects of the document that are the preset header, in `components/parameters` and inline."""
    for parameter in document.get("components", {}).get("parameters", {}).values():
        if _is_preset_parameter(parameter):
            yield parameter
    for operation in _operations(document):
        for parameter in operation.get("parameters", []):
            if _is_preset_parameter(parameter):
                yield parameter


def drop_preset_parameter(document: dict) -> None:
    """Leaves the preset header out of the document: the component and every operation's use of it."""
    components = document.get("components", {}).get("parameters", {})
    names = {name for name, parameter in components.items() if _is_preset_parameter(parameter)}
    refs = {_COMPONENT_PARAMETERS + name for name in names}
    for name in names:
        del components[name]
    for operation in _operations(document):
        if "parameters" in operation:
            operation["parameters"] = [parameter for parameter in operation["parameters"]
                                       if parameter.get("$ref") not in refs and not _is_preset_parameter(parameter)]


def key_rpp_bodies(document: dict, media_type: str) -> None:
    """Keys every RPP body (request and responses; a Problem Detail is another media type) by `media_type`."""
    for operation in _operations(document):
        contents = [operation["requestBody"].get("content", {})] if "requestBody" in operation else []
        contents += [response.get("content", {}) for response in operation.get("responses", {}).values()]
        for content in contents:
            if RPP_MEDIA_TYPE in content:
                content[media_type] = content.pop(RPP_MEDIA_TYPE)


def require_content_type(document: dict, media_type: str) -> None:
    """Gives every operation without a request body a required `Content-Type` header parameter of `media_type` alone: the
    request preset of such a request is that of its `Content-Type` too, the default preset without one (core §13). OAS 3.1
    has a `Content-Type` header parameter ignored, but a UI that sends it (Scalar) then reads with the document's preset (#205)."""
    document.setdefault("components", {}).setdefault("parameters", {})[CONTENT_TYPE_PARAMETER] = {
        "name": "Content-Type", "in": "header", "required": True,
        "description": "The preset of this request (media type signalling): a request without content is the default "
                       "preset's without it.",
        "schema": {"type": "string", "enum": [media_type], "default": media_type}}
    for operation in _operations(document):
        if "requestBody" not in operation:
            operation.setdefault("parameters", []).append({"$ref": _COMPONENT_PARAMETERS + CONTENT_TYPE_PARAMETER})
