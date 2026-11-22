from urllib.parse import quote

from rpp.schema.effective_schema import compose
from rpp.schema.offered_preset import OfferedPreset
from rpp.schema.offered_presets import OfferedPresets
from rpp.schema.schema_scope import SchemaScope

JSON_SCHEMA = "https://json-schema.org/draft/2020-12/schema"
MEDIA_TYPE = "application/schema+json"


def schema_path(preset_id: str) -> str:
    """The path of the `schema` sub-resource of a preset (core Rule 3); the identifier is one path segment."""
    return f"/presets/{quote(preset_id, safe=':')}/schema"


def schema_url(base_url: str, preset_id: str) -> str:
    return base_url.rstrip("/") + schema_path(preset_id)


class PresetSchemas:
    """The Preset Schema of each offered preset (json §Preset Schema) and its validators, built once when the app is built
    and then only read. The document is self-contained, has no `unevaluatedProperties` (a validator adds them) and, when the
    server has a public base URL, the URL of the sub-resource as `$id`."""

    def __init__(self, presets: OfferedPresets, base_url: str | None):
        # a request is checked against the profiles the proxy checks; the document states all that apply
        self._scopes = {item.id: SchemaScope(item.extensions, item.checked, item.required) for item in presets.offered}
        self._documents = {item.id: self._document(item, base_url) for item in presets.offered}

    @staticmethod
    def _document(item: OfferedPreset, base_url: str | None) -> dict:
        document = {"$schema": JSON_SCHEMA}
        if base_url:
            document["$id"] = schema_url(base_url, item.id)
        document["rpp:preset"] = {"id": item.id, "version": item.version}
        document["$defs"] = compose(item.extensions, item.applicable, False, item.required)
        return document

    def scope_of(self, item: OfferedPreset) -> SchemaScope:
        return self._scopes[item.id]

    def document_of(self, item: OfferedPreset) -> dict:
        return self._documents[item.id]
