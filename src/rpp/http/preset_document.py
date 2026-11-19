from dataclasses import dataclass


@dataclass(frozen=True)
class PresetDocument:
    """The OpenAPI document of one offered preset (#205): its id and version, and the document."""

    preset_id: str
    version: str
    document: dict
