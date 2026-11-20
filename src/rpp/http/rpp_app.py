import copy

from connexion import FlaskApp


class RppApp(FlaskApp):
    """The RPP app, which also gives its effective OpenAPI documents (#205). It serves none: that is `api_docs`'s."""

    def __init__(self, import_name: str, *, openapi_documents: tuple[dict, ...], **kwargs):
        super().__init__(import_name, **kwargs)
        self._openapi_documents = openapi_documents

    def openapi_documents(self) -> tuple[dict, ...]:
        """The default document first (#204: the default preset's body schemas, no preset stated), then the effective OpenAPI of
        each offered preset, the default preset's first (#205: its body schemas and API, the preset stated as the server's
        signalling takes it). OpenAPI 3.1, each naming its preset in `info.x-rpp-preset`; copies, made when the app is built."""
        return copy.deepcopy(self._openapi_documents)
