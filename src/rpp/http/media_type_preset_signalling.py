from decimal import Decimal

from connexion import ProblemException

from core.result.result_code import ResultCode
from rpp.http import media_range
from rpp.http.asgi_headers import request_values, rewriting_start, values_of, without
from rpp.http.document_signalling import drop_preset_parameter, key_rpp_bodies
from rpp.http.headers import RPP_MEDIA_TYPE, problem_headers
from rpp.http.media_range import MediaRange
from rpp.http.media_range_error import MediaRangeError
from rpp.http.preset_header import HEADER as PRESET_HEADER
from rpp.http.preset_selection import PresetSelection
from rpp.http.vary import vary_with
from rpp.schema.offered_preset import OfferedPreset
from rpp.schema.offered_presets import OfferedPresets

# What a media range of an Accept says about a preset, from the least to the most specific (RFC 9110 §12.5.1).
ANY, ANY_APPLICATION, DEFAULT_ONLY, EXACT = 0, 1, 2, 3


def preset_media_type(preset: OfferedPreset) -> str:
    """The RPP media type with the parameters of `preset` (core §Media Type Signalling), as a response is typed with it."""
    return f'{RPP_MEDIA_TYPE}; preset="{preset.id}"; preset-version="{preset.version}"'


def _refused(status: int, code: ResultCode, detail: str) -> ProblemException:
    return ProblemException(
        status=status, title=code.value[1], detail=detail,
        headers={**problem_headers(code), "Vary": "Accept"})


class MediaTypePresetSignalling:
    """Selects the preset of a request with the media type parameters `preset` and `preset-version` (core §Media Type Signalling),
    and shows the applied one in the `Content-Type` of the response.

    The request preset is that of the request's `Content-Type`, for every request with content or without (§13 asks
    for one on every request; a missing one, or one without the parameters, is the default preset). The response
    preset is chosen from `Accept` by weight (core §13, RFC 9110 §12.5.1). A range with the preset parameters stands for that preset. An `application/rpp+json`
    range without them stands for the default preset, as a request without parameters gets it (core §Media Type Signalling), and
    `application/*` and `*/*` for every preset offered. The most specific range that matches a preset gives its weight;
    a weight of 0 excludes it. Of the presets of the highest weight the request preset is answered if it is among
    them, else that of the first range of the Accept (the default, if a wildcard is that range). Without an `Accept` the default preset is acceptable.

    The refusals are 415 for a preset or version of the `Content-Type` that the server does not offer, 406 when none of
    the `Accept` is, and 400 when the request preset is not listed in the `Accept`, when a value cannot be read, and for
    the `RPP-Preset` header (both methods in use, §14). Each has an RPP result code and `Vary: Accept`. The response
    carries no `RPP-Preset` header, which would be the second method (§14).
    """

    def __init__(self, presets: OfferedPresets):
        self._presets = presets

    def resolve(self, scope) -> PresetSelection:
        # Core §14: the two methods MUST NOT be used simultaneously.
        if request_values(scope, PRESET_HEADER):
            raise _refused(400, ResultCode.COMMAND_SYNTAX_ERROR,
                           "This server signals the preset with the media type parameters preset and "
                           f"preset-version: the {PRESET_HEADER} header field is not used")
        try:
            ranges = media_range.parse_accept(request_values(scope, "Accept"))
            request = self._request_preset(scope)
            weights = self._acceptable(ranges)
        except MediaRangeError as error:
            raise _refused(400, error.code, str(error)) from None
        if not weights:
            raise _refused(406, ResultCode.PARAMETER_VALUE_RANGE_ERROR,
                           "The Accept field lists no preset this server offers")
        if request.key not in weights:
            raise _refused(400, ResultCode.COMMAND_SYNTAX_ERROR,
                           f"The preset of the request, {request.id}, is not listed in the Accept field")
        best = max(quality for quality, _ in weights.values())
        tied = {key: position for key, (quality, position) in weights.items() if quality == best}
        if request.key in tied:
            chosen = request.key
        else:
            # one range (a wildcard) can stand for several: the default of the server is the one it means
            chosen = min(tied, key=lambda key: (tied[key], key != self._presets.default.key))
        return PresetSelection(request=request, response=next(
            preset for preset in self._presets.offered if preset.key == chosen))

    def _offered(self, name: str, version: Decimal) -> OfferedPreset | None:
        preset = self._presets.by_id(name)
        # compared as decimals, as the header method does: 1.10 is 1.1
        return preset if preset is not None and Decimal(preset.version) == version else None

    def _request_preset(self, scope) -> OfferedPreset:
        values = request_values(scope, "Content-Type")
        if len(values) > 1:
            raise MediaRangeError(ResultCode.PARAMETER_VALUE_SYNTAX_ERROR, "The request has several Content-Type fields")
        content_type = media_range.parse_media_type(values[0]) if values else None
        named = content_type.preset() if content_type is not None and content_type.kind == RPP_MEDIA_TYPE else None
        if named is None:
            return self._presets.default  # no parameters: the default preset (core §Media Type Signalling)
        preset = self._offered(*named)
        if preset is None:
            raise _refused(415, ResultCode.PARAMETER_VALUE_RANGE_ERROR,
                           f"This server does not offer version {named[1]} of the preset {named[0]} for requests")
        return preset

    def _acceptable(self, ranges: list[MediaRange]) -> dict[str, tuple[Decimal, int]]:
        """The offered presets of weight above 0, by key, with their weight and the position of the range that gave
        it."""
        if not ranges:
            return {self._presets.default.key: (Decimal(1), 0)}
        found: dict[str, tuple[int, Decimal, int]] = {}  # key -> (specificity, weight, position)
        for position, item in enumerate(ranges):
            for specificity, preset in self._matches(item):
                best = found.get(preset.key)
                if best is None or (specificity, item.quality) > best[:2]:
                    found[preset.key] = (specificity, item.quality, position)
        return {key: (weight, position) for key, (_, weight, position) in found.items() if weight > 0}

    def _matches(self, item: MediaRange):
        """The presets a range stands for, with how specific the range is."""
        if item.kind == "*/*":
            return [(ANY, preset) for preset in self._presets.offered]
        if item.kind == "application/*":
            return [(ANY_APPLICATION, preset) for preset in self._presets.offered]
        if item.kind != RPP_MEDIA_TYPE:
            return []
        named = item.preset()
        if named is None:
            return [(DEFAULT_ONLY, self._presets.default)]
        preset = self._offered(*named)
        return [(EXACT, preset)] if preset is not None else []

    def announce(self, send, selection: PresetSelection):
        """`send` that gives an RPP response (a Problem Detail is another media type) the preset applied in its
        `Content-Type` (core §Media Type Signalling), and lists `Accept` in `Vary`."""
        applied = preset_media_type(selection.response)

        def rewrite(status, headers):
            vary = ", ".join(values_of(headers, "Vary"))
            headers = [*without(headers, "Vary"), (b"vary", vary_with(vary, "Accept").encode("latin-1"))]
            # any RPP answer, an availability 404 included: core §13 has a client refuse an RPP type it did not ask for
            if [value.lower() for value in values_of(headers, "Content-Type")] == [RPP_MEDIA_TYPE]:
                headers = [*without(headers, "Content-Type"), (b"content-type", applied.encode("latin-1"))]
            return headers
        return rewriting_start(send, rewrite)

    def state_in(self, document: dict, preset: OfferedPreset) -> None:
        """Makes `document`, the OpenAPI document of `preset` (#205), send it: every RPP body is keyed by the preset's media
        type, which a client then sends as `Content-Type` and `Accept`, and `RPP-Preset`, which this method refuses, is left out."""
        drop_preset_parameter(document)
        key_rpp_bodies(document, preset_media_type(preset))

    def problem_headers(self, selection: PresetSelection, headers: dict) -> dict:
        """The headers of a Problem Detail rendered after the selection: no preset parameters, no `RPP-Preset`."""
        return {**headers, "Vary": vary_with(headers.get("Vary"), "Accept")}
