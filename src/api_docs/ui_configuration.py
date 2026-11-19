from api_docs.served_documents import ServedDocuments, preset_document_path

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


def ui_configuration(documents: ServedDocuments, base_path: str) -> dict:
    """The configuration of the UI page: a source per preset document, the default preset's first and chosen."""
    sources = []
    for index, document in enumerate(documents.presets):
        preset = document["info"]["x-rpp-preset"]
        sources.append({"title": f"{preset['id']} {preset['version']}" + (" (default)" if index == 0 else ""),
                        "url": base_path + preset_document_path(preset["id"]), **({"default": True} if index == 0 else {})})
    return {**UI_CONFIGURATION, "sources": sources}
