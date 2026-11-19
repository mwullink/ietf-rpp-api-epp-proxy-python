from connexion.middleware.swagger_ui import SwaggerUIMiddleware

from rpp.http.middleware.served_documents_api import ServedDocumentsAPI
from rpp.http.served_documents import ServedDocuments
from rpp.http.served_specification import ServedSpecification


class ServedDocumentsMiddleware(SwaggerUIMiddleware):
    """Connexion's UI middleware, which serves the documents it is given instead of the spec Connexion routes with:
    `/openapi.json` and `/openapi.yaml` the default preset's (`served_document`, OpenAPI 3.1, #204), `/openapi/{preset-id}.json`
    and `.yaml` each offered preset's (#205), and `/ui/` the UI over them.

    The documents are their own, made when the app is built: Connexion's response validation, which writes `components` into the
    response schemas of the spec its middlewares share, does not reach them (#193). `create_app` gives them per app
    (`functools.partial`), as Connexion builds a middleware with the app alone."""

    def __init__(self, app, documents: ServedDocuments):
        super().__init__(app)
        self._documents = documents

    def add_api(self, specification, base_path=None, arguments=None, **kwargs) -> None:  # noqa: ARG002 - served are its own
        api = ServedDocumentsAPI(ServedSpecification(self._documents.default), base_path=base_path, arguments=arguments,
                                 default=self.default_fn, documents=self._documents, **kwargs)
        self.router.mount(api.base_path, app=api.router)
