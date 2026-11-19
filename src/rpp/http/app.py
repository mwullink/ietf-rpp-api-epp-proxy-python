import copy
from functools import partial
from functools import cache
from pathlib import Path

import yaml
from connexion import FlaskApp
from connexion.datastructures import MediaTypeDict
from connexion.exceptions import ProblemException
from connexion.middleware import ConnexionMiddleware, MiddlewarePosition
from connexion.middleware.swagger_ui import SwaggerUIMiddleware
from connexion.options import SwaggerUIOptions
from connexion.validators import VALIDATOR_MAP
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware

from core.capabilities.backend_profile import BackendProfile
from rpp.http.context import BACKEND_PROFILE, DISCOVERY_SETTINGS, OFFERED_PRESETS, PRESET_SCHEMAS, REQUEST_PRESETS
from rpp.http.middleware.body_buffering_middleware import BodyBufferingMiddleware
from rpp.http.problem import handle_http_exception, handle_rpp_error
from rpp.http.preset_middleware import PresetMiddleware
from rpp.http.preset_signalling import HEADER_SIGNALLING, preset_signalling
from rpp.http.request_presets import RequestPresets
from rpp.http.middleware.line_feed_path_middleware import LineFeedPathMiddleware
from rpp.http.middleware.served_documents_middleware import ServedDocumentsMiddleware
from rpp.http.preset_document import PresetDocument
from rpp.http.served_documents import ServedDocuments
from rpp.http.security.bearer_refusing_security_handler import BearerRefusingSecurityHandler
from rpp.http.security.session_security_handler import SessionSecurityHandler
from rpp.http.validators.rpp_request_body_validator import RppRequestBodyValidator
from rpp.http.validators.rpp_response_body_validator import RppResponseBodyValidator
from registration import ExtensionRegistry
from rpp.http.body_definitions import mark_body_definitions
from rpp.http.extension_paths import add_extension_paths, add_registered_paths, collections
from rpp.http.served_document import served_document
from rpp.http.extension_resolver import ExtensionResolver
from rpp.schema.bundle_definitions import bundle_definitions
from rpp.schema.extensions import EXTENSIONS, check_known, own_definitions
from rpp.schema.https_url import https_url
from rpp.schema.definitions import Definitions
from rpp.schema.offered_presets import OfferedPresets
from rpp.schema.preset_schemas import PresetSchemas

OPENAPI_SPEC = Path(__file__).parent.parent / "openapi.yaml"

# Scalar, which shows a document per offered preset (#205): the files of @scalar/api-reference, see its README.md.
SCALAR_UI = Path(__file__).parent / "scalar_ui"


@cache
def parsed_spec() -> dict:
    """
    The OpenAPI document, parsed once per process with libyaml, because parsing it takes most of the time an app
    takes to build (#112). Callers get it shared: copy it before handing it on.
    """
    with OPENAPI_SPEC.open("rb") as spec:
        return yaml.load(spec, Loader=yaml.CSafeLoader)


def public_base_url(discovery_settings) -> str | None:
    """The base URL the discovery document states, None where there is none to state (unset, not an acceptable https URL:
    no userinfo, query or fragment, or settings that cannot be read: discovery answers that at request time). An unauthenticated
    endpoint publishes it in a `$id`, so it must be one discovery would state."""
    try:
        url = getattr(discovery_settings, "rpp_base_url", None)
    except Exception:  # noqa: BLE001 - settings are read by the request that needs them
        return None
    return url if https_url(url) else None


def omitted_operations(openapi_settings, held_objects, extension_ids, resolver: ExtensionResolver):
    """What the document served leaves out (`rpp_openapi_omit_*`, nothing without settings): the operations on a data object
    the backend does not hold, and those no handler serves. None where it leaves out nothing."""
    unheld = bool(getattr(openapi_settings, "rpp_openapi_omit_unheld_objects", False))
    unimplemented = bool(getattr(openapi_settings, "rpp_openapi_omit_unimplemented", False))
    if not (unheld or unimplemented):
        return None
    segments = collections(extension_ids)

    def omit(path: str, operation: dict) -> bool:
        obj = segments.get(path.lstrip("/").split("/", 1)[0])
        if unheld and obj is not None and obj not in held_objects:
            return True
        return unimplemented and not resolver.implements(operation.get("operationId", ""))
    return omit


def outside_the_preset(item, presets: OfferedPresets, omit):
    """`omit`, and the operations on a data object of an extension the preset does not contain: a request under it is refused
    (400, core RC4), so they are no part of its API (#205)."""
    own = set(collections(item.extension_ids).values())
    foreign = {segment for segment, obj in collections(presets.extension_ids()).items() if obj not in own}

    def outside(path: str, operation: dict) -> bool:
        return path.lstrip("/").split("/", 1)[0] in foreign or (omit is not None and omit(path, operation))
    return outside


def preset_documents(spec, presets: OfferedPresets, preset_schemas: PresetSchemas, request_presets: RequestPresets, signalling,
                     openapi_settings, resolver: ExtensionResolver) -> tuple[PresetDocument, ...]:
    """The OpenAPI document of each offered preset, the default preset's first (#205): the preset's body schemas, what it does
    not hold or no handler serves left out as the switches say, the objects of extensions it does not contain left out, and the
    preset stated as `signalling` takes it."""
    documents = []
    for item in (presets.default, *(other for other in presets.offered if other is not presets.default)):
        omit = omitted_operations(openapi_settings, request_presets.profile_of(item).objects, presets.extension_ids(), resolver)
        document = served_document(spec, preset_schemas.document_of(item), item.extension_ids,
                                   outside_the_preset(item, presets, omit))
        signalling.state_in(document, item)
        documents.append(PresetDocument(preset_id=item.id, version=item.version, document=document))
    return tuple(documents)


def create_app(sessions, profile: BackendProfile, discovery_settings=None, signalling=HEADER_SIGNALLING,
               registry: ExtensionRegistry | None = None, openapi_settings=None):
    """
    Builds the application.

    Args:
        sessions: The `SessionPool`, which gives the registry backend of the request's user, or None to reject the
            request.
        profile: What the backend can hold, which the mappers check, refusals name and discovery states.
        discovery_settings: Has rpp_base_url, rpp_tlds, rpp_environment_name and
            rpp_environment_status, which the discovery document states.
        signalling: How a client names the preset of a request (`rpp_preset_signalling`): `header` or `media-type`.
        registry: The extensions this app registered (`rpp_extensions`): their paths and handlers are the app's, and
            only its. Without it the app is the drafts' and the extensions of the proxy's own.
        openapi_settings: Has rpp_openapi_omit_unheld_objects and rpp_openapi_omit_unimplemented, what the OpenAPI document
            served leaves out. None leaves out nothing, as the drafts' API contract has it.
    """
    registry = registry or ExtensionRegistry()
    check_known(profile.extensions)
    definitions = Definitions.load(registry, EXTENSIONS)
    presets = OfferedPresets.build(definitions, profile.presets, profile.default_preset, profile.bound_profiles,
                                   profile.extensions)
    # The Preset Schemas and their validators are built here, once, per app, and only read by a request. A base URL that
    # discovery would refuse is no public URL: the documents then have no `$id`.
    preset_schemas = PresetSchemas(presets, public_base_url(discovery_settings))
    request_presets = RequestPresets(profile, presets, preset_schemas)
    # connexion changes the spec it is given, so each app gets its own copy. Each body that stands for a definition is marked
    # with it, which the body validators validate with under the request's preset; the documents served are OpenAPI 3.1, with
    # the definitions of the default preset (#204) and of each offered preset (#205).
    spec = add_registered_paths(add_extension_paths(copy.deepcopy(parsed_spec()), presets.extension_ids()), registry)
    spec = mark_body_definitions(spec, {*bundle_definitions(), *own_definitions(presets.extension_ids())})
    resolver = ExtensionResolver('rpp.handlers', registry.handler_packages())
    omit = omitted_operations(openapi_settings, request_presets.profile_of(presets.default).objects, presets.extension_ids(),
                              resolver)
    served = served_document(spec, preset_schemas.document_of(presets.default), presets.default.extension_ids, omit)
    method = preset_signalling(signalling, presets)
    documents = ServedDocuments(served, preset_documents(spec, presets, preset_schemas, request_presets, method, openapi_settings,
                                                         resolver))
    app = FlaskApp(
        __name__,
        security_map={"basic": lambda: SessionSecurityHandler(sessions), "bearer": BearerRefusingSecurityHandler},
        middlewares=[partial(ServedDocumentsMiddleware, documents=documents) if middleware is SwaggerUIMiddleware
                     else middleware for middleware in ConnexionMiddleware.default_middlewares],
    )
    app.add_middleware(LineFeedPathMiddleware, position=MiddlewarePosition.BEFORE_ROUTING)
    app.add_middleware(BodyBufferingMiddleware, position=MiddlewarePosition.BEFORE_VALIDATION)
    app.add_middleware(PresetMiddleware, position=MiddlewarePosition.BEFORE_VALIDATION,
                       signalling=method, request_presets=request_presets,
                       extensions=presets.extension_ids())
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_api(spec, resolver=resolver, resolver_error=501,
                validate_responses=True, swagger_ui_options=SwaggerUIOptions(swagger_ui_template_dir=str(SCALAR_UI)),
                validator_map={
                    "body": MediaTypeDict({**VALIDATOR_MAP["body"], "*/*json": RppRequestBodyValidator}),
                    "response": MediaTypeDict({"*/*json": RppResponseBodyValidator}),
                })
    app.app.config[DISCOVERY_SETTINGS] = discovery_settings
    app.app.config[BACKEND_PROFILE] = profile
    app.app.config[OFFERED_PRESETS] = presets
    app.app.config[PRESET_SCHEMAS] = preset_schemas
    app.app.config[REQUEST_PRESETS] = request_presets
    app.add_error_handler(ProblemException, handle_rpp_error)
    app.add_error_handler(HTTPException, handle_http_exception)

    return app
