import json
from pathlib import Path

import yaml
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, PlainTextResponse, RedirectResponse, Response
from starlette.routing import Match, Route, Router
from starlette.templating import Jinja2Templates

from api_docs.served_documents import PRESET_DOCUMENTS, ServedDocuments
from api_docs.ui_configuration import ui_configuration

# Scalar, which shows a document per preset (#205): the files of @scalar/api-reference, see its README.md.
SCALAR_UI = Path(__file__).parent / "scalar_ui"


def _base_path(request: Request) -> str:
    """The path the app is served under (a reverse proxy's prefix, `root_path`), as Connexion gives it to a document."""
    return request.scope.get("root_path", "").rstrip("/")


class DocsApp:
    """The OpenAPI documents of an app and the UI over them, served in front of it (#205): `/openapi.json` and `/openapi.yaml`
    the default document, `/openapi/{preset-id}.json` and `.yaml` each preset's, `/ui/` Scalar with a source per preset. Every
    other request, and the lifespan, goes to the app.

    `documents` are plain OpenAPI documents, the default one first, then one per preset, each naming its preset in
    `info.x-rpp-preset`. Each is served with the base path of the request as its `servers`, and may be read from any origin."""

    def __init__(self, app, documents):
        self._app = app
        self._documents = ServedDocuments.of(documents)
        self._templates = Jinja2Templates(directory=str(SCALAR_UI))
        self._routes = [
            Route("/openapi.json", self._default_json, methods=["GET"]),
            Route("/openapi.yaml", self._default_yaml, methods=["GET"]),
            Route(PRESET_DOCUMENTS + "/{preset_id}.json", self._preset_json, methods=["GET"]),
            Route(PRESET_DOCUMENTS + "/{preset_id}.yaml", self._preset_yaml, methods=["GET"]),
            Route("/ui", self._to_ui, methods=["GET"]),
            Route("/ui/", self._ui, methods=["GET"]),
            Route("/ui/standalone.js", self._bundle, methods=["GET"]),
        ]
        self._served = CORSMiddleware(Router(routes=self._routes, redirect_slashes=False), allow_origins=["*"],
                                      allow_methods=["GET"])

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and any(route.matches(scope)[0] is not Match.NONE for route in self._routes):
            await self._served(scope, receive, send)
        else:
            await self._app(scope, receive, send)

    def _served_document(self, document: dict | None, request: Request) -> dict | None:
        if document is None:
            return None
        return {**json.loads(json.dumps(document)), "servers": [{"url": _base_path(request)}]}

    @staticmethod
    def _json(document: dict | None) -> Response:
        if document is None:
            return PlainTextResponse("Not Found", status_code=404)
        return Response(json.dumps(document), media_type="application/json")

    @staticmethod
    def _yaml(document: dict | None) -> Response:
        if document is None:
            return PlainTextResponse("Not Found", status_code=404)
        return Response(yaml.safe_dump(document, allow_unicode=True), media_type="text/yaml")

    async def _default_json(self, request: Request) -> Response:
        return self._json(self._served_document(self._documents.default, request))

    async def _default_yaml(self, request: Request) -> Response:
        return self._yaml(self._served_document(self._documents.default, request))

    async def _preset_json(self, request: Request) -> Response:
        return self._json(self._served_document(self._documents.of_preset(request.path_params["preset_id"]), request))

    async def _preset_yaml(self, request: Request) -> Response:
        return self._yaml(self._served_document(self._documents.of_preset(request.path_params["preset_id"]), request))

    async def _to_ui(self, request: Request) -> Response:
        return RedirectResponse(_base_path(request) + "/ui/")

    async def _ui(self, request: Request) -> Response:
        return self._templates.TemplateResponse(
            request, name="index.j2", context={"configuration": ui_configuration(self._documents, _base_path(request))})

    async def _bundle(self, request: Request) -> Response:  # noqa: ARG002 - the same file for every request
        return FileResponse(SCALAR_UI / "standalone.js", media_type="text/javascript")
