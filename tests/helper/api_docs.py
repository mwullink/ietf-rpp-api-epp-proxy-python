"""An rpp app with its documents served in front of it, as `main.compose` puts them together (#205)."""
from starlette.testclient import TestClient

from api_docs.docs_app import DocsApp


def served_client(app) -> TestClient:
    return TestClient(DocsApp(app, app.openapi_documents()))
