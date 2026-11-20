# Scalar

`standalone.js` is `dist/browser/standalone.js` of `@scalar/api-reference` 1.76.4 (npm, MIT, `LICENSE` from the repository
`scalar/scalar`), sha256 `k5UfF5SwRjuHq1jQVXpmEAda95qflMKj8mHJk7x/ORM=`. `index.j2` is the page `DocsApp` renders at `/ui/`,
with the configuration of `ui_configuration.py`: a source per offered preset (#205), and none of
Scalar's platform (developer tools, AI agent, MCP, telemetry, fonts from Scalar's servers, the link to its hosted client), so that
no request leaves the server's origin; code snippets HTTP/1.1 (the default) and curl.

To update: replace `standalone.js` by that of a newer release at least two weeks old, the version and hash above, and the
version the unit test checks (`tests/unit/test_openapi_preset_documents.py`); check that the options of `UI_CONFIGURATION` and
the snippet targets of `_HIDDEN_TARGETS` (`ui_configuration.py`) still exist in it, and that the page loads nothing from
another origin.
