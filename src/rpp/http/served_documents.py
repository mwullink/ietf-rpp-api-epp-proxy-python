from dataclasses import dataclass
from urllib.parse import quote

from rpp.http.preset_document import PresetDocument

PRESET_DOCUMENTS = "/openapi"


def preset_document_path(preset_id: str) -> str:
    """The path of a preset's OpenAPI document, outside the RPP paths (#205)."""
    return f"{PRESET_DOCUMENTS}/{quote(preset_id, safe=':')}.json"


@dataclass(frozen=True)
class ServedDocuments:
    """The OpenAPI documents an app serves: `default`, the default preset's (`/openapi.json`, #204), and one per offered preset
    (#205), the default preset's first. Made when the app is built, only read by a request."""

    default: dict
    presets: tuple[PresetDocument, ...]

    def of(self, preset_id: str) -> PresetDocument | None:
        return next((item for item in self.presets if item.preset_id == preset_id), None)
