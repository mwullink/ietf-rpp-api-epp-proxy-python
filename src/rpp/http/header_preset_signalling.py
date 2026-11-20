from decimal import Decimal

from connexion import ProblemException

from core.result.result_code import ResultCode
from rpp.http import preset_header
from rpp.http.asgi_headers import request_values, rewriting_start, values_of, without
from rpp.http.document_signalling import preset_parameters
from rpp.http.headers import problem_headers
from rpp.http.preset_selection import PresetSelection
from rpp.schema.offered_preset import OfferedPreset
from rpp.schema.offered_presets import OfferedPresets


def _refused(code: ResultCode, detail: str) -> ProblemException:
    return ProblemException(status=400, title=code.value[1], detail=detail, headers=problem_headers(code))


class HeaderPresetSignalling:
    """Selects the preset of a request with the `RPP-Preset` header field (core §Header Signalling), and shows the applied
    one in the response.

    A request that names none gets the default preset of the server (core RC1). It raises a `ProblemException` (400, with an
    RPP client error code) for a value it cannot read or a preset or version the server does not offer. The parameters of
    the media type mean the other method, so they are refused. The request and the response have one preset.
    """

    def __init__(self, presets: OfferedPresets):
        self._presets = presets

    def resolve(self, scope) -> PresetSelection:
        return PresetSelection.of(self._resolve(scope))

    def _resolve(self, scope) -> OfferedPreset:
        # Core §Preset Signalling: the two methods MUST NOT be used simultaneously.
        if preset_header.has_preset_parameters(request_values(scope, "Accept") + request_values(scope, "Content-Type")):
            raise _refused(ResultCode.COMMAND_SYNTAX_ERROR,
                           "This server signals the preset with the RPP-Preset header field: "
                           "the media type takes no preset parameters")
        try:
            named = preset_header.parse(request_values(scope, preset_header.HEADER))
        except preset_header.PresetHeaderError as error:
            raise _refused(error.code, str(error)) from None
        if named is None:
            return self._presets.default
        identifier, version = named
        preset = self._presets.by_id(identifier)
        if preset is None:
            raise _refused(ResultCode.PARAMETER_VALUE_RANGE_ERROR, f"This server does not offer the preset {identifier}")
        if Decimal(preset.version) != version:  # compared as decimals: 1.10 is 1.1 (RFC 9651)
            raise _refused(ResultCode.PARAMETER_VALUE_RANGE_ERROR,
                           f"This server does not offer version {version} of the preset {identifier}")
        return preset

    def announce(self, send, selection: PresetSelection):
        """`send` that adds the `RPP-Preset` header of the applied preset to the response (core §Header Signalling)."""
        preset = selection.response

        def rewrite(status, headers):
            vary = ", ".join(values_of(headers, "Vary"))
            return [*without(headers, "Vary"), (preset_header.HEADER.lower().encode(),
                                                preset_header.format_preset(preset).encode()),
                    (b"vary", preset_header.vary_with_preset(vary).encode("latin-1"))]
        return rewriting_start(send, rewrite)

    def state_in(self, document: dict, preset: OfferedPreset) -> None:
        """Makes `document`, the OpenAPI document of `preset` (#205), send it: its `RPP-Preset` is required, with the preset as
        its only value and its default, as a response names it."""
        value = preset_header.format_preset(preset)
        for parameter in preset_parameters(document):
            parameter["required"] = True
            parameter["schema"] = {"type": "string", "enum": [value], "default": value}

    def problem_headers(self, selection: PresetSelection, headers: dict) -> dict:
        """The headers of a Problem Detail rendered after the selection."""
        return {**headers, preset_header.HEADER: preset_header.format_preset(selection.response),
                "Vary": preset_header.vary_with_preset(headers.get("Vary"))}
