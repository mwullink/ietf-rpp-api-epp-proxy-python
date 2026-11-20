import json
from dataclasses import dataclass
from urllib.parse import quote

PRESET_DOCUMENTS = "/openapi"


def preset_id(document: dict) -> str:
    """The preset a document is of, as it names it (`info.x-rpp-preset`)."""
    return document["info"]["x-rpp-preset"]["id"]


def preset_document_path(preset: str) -> str:
    """The path of a preset's document, outside the RPP paths (#205)."""
    return f"{PRESET_DOCUMENTS}/{quote(preset, safe=':')}.json"


@dataclass(frozen=True)
class ServedDocuments:
    """The OpenAPI documents served: `default` at `/openapi.json` (#204), and one per preset (#205), the default preset's first.
    Copies of those given, so that nothing else changes them."""

    default: dict
    presets: tuple[dict, ...]

    @classmethod
    def of(cls, documents) -> "ServedDocuments":
        """`documents`: the default document first, then one per preset."""
        copies = tuple(json.loads(json.dumps(document)) for document in documents)
        return cls(default=copies[0], presets=copies[1:])

    def of_preset(self, preset: str) -> dict | None:
        return next((document for document in self.presets if preset_id(document) == preset), None)
