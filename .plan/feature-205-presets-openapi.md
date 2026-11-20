# Plan: #205 every offered preset in the OpenAPI document (Story 6 of #174)

Branch `feature/205-presets-openapi` from `main` (e6fa249). Clean-main step: the local changes to `.vscode/settings.json`,
`deploy/ansible/ansible.cfg` and the untracked `config.rri-mtest.yaml.local`, `demo`, `.demo` are carried, never committed
(as in #204).

## Findings of the experiment (evidence)

Reproducers and the demo of the variants: `~/rpp-205-demo/` (outside the repository; `start.sh` serves documents built from
the served document of #204 for each preset of `config.demo-extended.yaml`, a header proxy on :8001, a media-type proxy on
:8002). UIs run in headless Chromium (Playwright), requests captured and sent to the real demo proxies.

- F1 A media type with parameters is a valid key of `content` in OpenAPI 3.1 (`openapi-spec-validator` 0.7.1).
- F2 Connexion 3.2 cannot choose a body schema by media type parameters: `split_content_type` drops them before the lookup.
  Only parameter keys: every request 415 `Invalid Content-type (application/rpp+json)`. With a bare key as well: every preset
  validated with the bare key's schema. Not needed: since #204 the routing spec keeps the bare key and our body validators
  validate with the signalled preset under both methods (D2 of #204).
- F3 Header signalling, one document: `oneOf` of the presets' schemas without a discriminator refuses a body valid under two
  presets; `anyOf` accepts an extension member under a preset without it. No UI ties an `RPP-Preset` enum to the body (Swagger UI,
  Scalar, Redoc show the `oneOf` branch as a separate choice); none reads an `x-` map. Not expressible.
- F4 Media-type signalling, one document with a `content` entry per preset: Swagger UI 5.17.14 / 5.35.0 send `Content-Type` and
  `Accept` of the chosen preset; Elements and RapiDoc too (Elements lists every preset in `Accept`); Redoc shows the schema per
  media type, no try-it; Scalar's reference switches but its test client always sends the first entry.
- F5 One document per preset (both methods): Swagger UI (`urls` selector) and Scalar (`sources` switcher) send the right
  `RPP-Preset` / `Content-Type` and body; Elements, RapiDoc, Redoc have no document selector. End to end against the demo proxies:
  201 for `atmosphere` under `planets-atmosphere` / `planets-complete`, 400 `02001` under `planets`.
- F6 Scalar can be reduced to the API reference and its test client: `showDeveloperTools: 'never'` (Configure, Share, Generate
  SDK, Deploy API), `agent: {disabled: true}` (Ask AI), `mcp: {disabled: true}`, `telemetry: false`, `withDefaultFonts: false`
  (no `fonts.scalar.com`), and `.open-api-client-button {display: none}` (a link to `client.scalar.com`, no option). Then no
  request leaves the origin. `defaultHttpClient: {targetKey: 'http', clientKey: 'http1.1'}` and `hiddenClients` leave HTTP/1.1
  and curl only.
- F7 The drafts' header parameter `Accept` (required) shows as a field to fill in Scalar and Swagger UI, next to the `Accept` the
  UI sets from the response media type. OAS 3.1, Parameter Object (`name`): a header parameter named `Accept`, `Content-Type` or `Authorization`
  SHALL be ignored.
- F8 Scalar `@scalar/api-reference` is MIT. 1.80.0 (tested) was published 2026-11-17; the newest release at least two weeks old
  is 1.76.4 (2026-10-30).
- F9 1.76.4 rechecked (2026-11-19, same demo): the options of F6 exist and work (only "Test Request" visible, HTTP/1.1 and curl,
  no request leaves the origin), the `sources` switcher changes the document, and Test Request on `POST /planets` of a header
  document sends its `RPP-Preset`. The npm package has no LICENSE file; the MIT text is the repository's (`scalar/scalar`).

- F10 Media-type signalling, a request without a body (a read, discovery) from a preset's document in Scalar: no
  `Content-Type`, so the request preset is the default one, and an `Accept` that lists only the document's preset is 400 `02001`
  (real `/ui/` on `config.demo-bound.yaml`). A `Content-Type` header parameter (required, the preset's media type) added to the
  document makes Scalar send it: 200. OAS 3.1 says such a parameter SHALL be ignored. Body requests work (201, both methods).

## Decisions (maintainer, 2026-11-19)

- D1 One document per offered preset, for both signalling methods, shown with Scalar.
- D2 Scalar with the reference and the test client only (F6), snippets HTTP/1.1 (default) and curl.
- D3 (Q1) A preset's document is outside the RPP paths: `/openapi/{preset-id}.json` and `.yaml`.
- D4 (Q2) The drafts' `Accept` header parameter stays in the served documents.
- D5 (Q3) Scalar 1.76.4.
- D6 (Q4) The findings go to #205 and `.spec/spec-issues.md`.

## Design (accepted 2026-11-19)

- `served_document` is made for every offered preset when the app is built (its Preset Schema, its extensions, and the omit
  switches by the objects that preset holds). `/openapi.json` and `/openapi.yaml` stay the default preset's (unchanged).
- Each document states its preset's signalling, so the UI sends it:
  - header: the `RPP-Preset` parameter of that document is required with the preset as its only value and default
    (`preset_header.format_preset`).
  - media-type: each `application/rpp+json` body (request and response) is keyed by the preset's media type (the one
    `MediaTypePresetSignalling.announce` writes, made in one place), and the `RPP-Preset` parameter is left out (refused there).
- `/ui/` serves Scalar (vendored like Swagger UI now, with its version and update notes), with one source per offered preset,
  the default first, configured as D2. Swagger UI 5 and its vendored files go.
- Routing and validation do not change (F2): the request is validated with the signalled preset's schemas, 400 / 422 `02308`
  as in #204.

- D7 (Q5) Media-type signalling: every operation without a request body in a preset's document gets a required `Content-Type`
  header parameter of the preset's media type (`require_content_type`).
- D8 (Q6) C1 accepted.
- D9 (Q7) `swagger_ui_bundle` removed from requirements.txt.

- D10 (review of #210) Serving the OpenAPI documents and the UI is no part of `rpp`: a top-level package `api_docs`
  (Starlette, no Connexion, imports no project package) serves `/openapi.json`, `/openapi.yaml`, `/openapi/{preset-id}.json`
  and `.yaml`, and `/ui/` (Scalar) in front of the rpp app, and passes every other request to it. `rpp` only makes the
  documents: `create_app` returns an `RppApp` (a `FlaskApp`) whose `openapi_documents()` gives the default document (#204)
  first, then one per offered preset, the default preset's first. `main.compose` puts them together (`Composition.app` is
  what is served, `Composition.rpp_app` the rpp app). Contracts: `api-docs-standalone`; `rpp` never imports `api_docs`. A
  document of a preset that is not offered is a plain 404 (was a Problem Detail); the line-feed guard no longer sees the
  document and UI paths.

## Corrections

- C1 The omit switch of unheld objects does not leave a demo object out of the base preset's document: the backend holds it
  under every preset. A request to it under a preset without its extension is refused (400, core RC4), so a preset's document
  always leaves out the objects of the extensions the preset does not contain (`outside_the_preset` in `app.py`; not a switch,
  as the drafts' paths stay). `/openapi.json` is unchanged (#204). For the maintainer's review.

## Tasks

- [x] T0 Plan, findings, design for acceptance
- [x] T1 Tests first (unit): a document per offered preset, equal to `GET /presets/{id}/schema`'s definitions, valid 3.1; the
  signalling of each (header value / media type keys, no `RPP-Preset` under media-type); `/openapi.json` unchanged; a request
  under a non-default preset validated with its schemas (400 / 422 `02308`); `/ui/` serves Scalar with every preset, no
  external URL
- [x] T2 Documents per preset and their routes
- [x] T3 Scalar vendored and configured, Swagger UI removed
- [x] T4 Docs: architecture.project.md (served document, line feed note, structure), README.md, `.spec/spec-issues.md`
  (findings); findings in #205
- [x] T5 Checks: lint-imports, unit, smoke (MTEST included, see the check results)
- [x] T6 Tests first (D10): `api_docs` alone (fake app, plain documents: routes, base path, CORS, 404, passing on, lifespan);
  the rpp app serves no document and gives `openapi_documents()`; the served-document tests through the composed app
- [x] T7 `api_docs` package, `RppApp`, `main.compose`; the serving parts leave `rpp`
- [x] T8 Contracts (`root_packages`, `api-docs-standalone`, `rpp` never imports `api_docs`), architecture.project.md, README
- [x] T9 Checks

## Check results (after D10)

- `lint-imports`: 29 kept, 0 broken (a probe import `api_docs -> rpp` and `rpp -> api_docs` each breaks its contract).
- Unit: 2904 passed.
- Smoke: 190 passed, 440 skipped (selectors, `rri-local` without credentials). The run covers `epp-docker` and DENIC MTEST
  (`rri-mtest`: its credentials are in `.env`, this machine reaches it), so MTEST was not pending. The maintainer's own MTEST
  smoke run on a0ef906: successful (2026-11-20).
- uvicorn `main:app` on `config.demo-bound.yaml`: `/ui` 307, `/ui/`, `/ui/standalone.js`, `/openapi.json`, `.yaml`, a preset's
  document 200, an unknown preset 404, `/.well-known/rpp` 200 from the rpp app.
- Browser (real `/ui/`, Scalar 1.76.4, `config.demo-extended.yaml` and `config.demo-bound.yaml`): the sources of every preset, the
  default first; `POST /planets` from the `planets-atmosphere` document 201 under both methods, with its `RPP-Preset` / media type;
  nothing loaded from another origin.

## Answered questions

- Q5 F10: under media-type signalling, give the operations without a request body a `Content-Type` header parameter (required,
  the preset's media type) in a preset's document, so that a read from the UI uses the preset (against OAS's "SHALL be ignored",
  but Scalar sends it)? Or leave it, and say in the document that a read needs `Content-Type`? Or file an issue on the server's
  rule (request preset of a request without a body)?
- Q6 C1: accept that a preset's document leaves out the objects of the extensions the preset does not contain?
- Q7 `swagger_ui_bundle` in requirements.txt is unused (since #204, the UI is vendored): remove it?
