from connexion.jsonifier import Jsonifier
from connexion.middleware.swagger_ui import SwaggerUIAPI
from connexion.utils import yamldumper
from starlette.exceptions import HTTPException
from starlette.responses import Response

from rpp.http.served_documents import PRESET_DOCUMENTS, ServedDocuments, preset_document_path
from rpp.http.served_specification import ServedSpecification

# The snippet targets of Scalar 1.76.4 (`hiddenClients`): every one is hidden but HTTP/1.1 and curl (#205).
_HIDDEN_TARGETS = ("c", "csharp", "clojure", "dart", "fsharp", "go", "java", "js", "julia", "kotlin", "node", "objc", "ocaml",
                   "php", "powershell", "python", "r", "ruby", "rust", "swift")

# Scalar with its API reference and its test client only (#205): no developer tools (Configure, Share, Generate SDK, Deploy
# API), no AI agent, no MCP, no telemetry, no fonts from Scalar's servers. With the hosted client's link hidden by `index.j2`,
# no request leaves the server's origin.
UI_CONFIGURATION = {
    "showDeveloperTools": "never",
    "agent": {"disabled": True},
    "mcp": {"disabled": True},
    "telemetry": False,
    "withDefaultFonts": False,
    "defaultHttpClient": {"targetKey": "http", "clientKey": "http1.1"},
    "hiddenClients": {**dict.fromkeys(_HIDDEN_TARGETS, True), "shell": ["httpie", "wget"]},
}


class ServedDocumentsAPI(SwaggerUIAPI):
    """Connexion's API of the served documents, with the documents of the offered presets (#205) at
    `/openapi/{preset-id}.json` and `.yaml`, each with the base path of the request (`servers`), as `/openapi.json` is; and its
    UI page rendered with the UI's configuration: a source per offered preset, the default preset's first."""

    def __init__(self, *args, documents: ServedDocuments, **kwargs):
        super().__init__(*args, **kwargs)
        self._documents = documents
        self._specifications = {item.preset_id: ServedSpecification(item.document) for item in documents.presets}
        self.router.add_route(methods=["GET"], path=PRESET_DOCUMENTS + "/{preset_id}.json", endpoint=self._get_preset_json)
        self.router.add_route(methods=["GET"], path=PRESET_DOCUMENTS + "/{preset_id}.yaml", endpoint=self._get_preset_yaml)

    def _preset_document(self, request) -> dict:
        specification = self._specifications.get(request.path_params["preset_id"])
        if specification is None:
            raise HTTPException(status_code=404)
        return specification.with_base_path(self._base_path_for_prefix(request)).raw

    async def _get_preset_json(self, request):
        return Response(content=Jsonifier().dumps(self._preset_document(request)), media_type="application/json")

    async def _get_preset_yaml(self, request):
        return Response(content=yamldumper(self._preset_document(request)), media_type="text/yaml")

    async def _get_swagger_ui_home(self, req):
        base_path = self._base_path_for_prefix(req)
        sources = [{"title": f"{item.preset_id} {item.version}" + (" (default)" if index == 0 else ""),
                    "url": base_path + preset_document_path(item.preset_id), **({"default": True} if index == 0 else {})}
                   for index, item in enumerate(self._documents.presets)]
        return self._templates.TemplateResponse(req, name="index.j2",
                                                context={"configuration": {**UI_CONFIGURATION, "sources": sources}})
