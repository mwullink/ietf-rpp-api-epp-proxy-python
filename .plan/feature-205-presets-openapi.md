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

## Tasks

- [x] T0 Plan, findings, design for acceptance
- [~] T1 Tests first (unit): a document per offered preset, equal to `GET /presets/{id}/schema`'s definitions, valid 3.1; the
  signalling of each (header value / media type keys, no `RPP-Preset` under media-type); `/openapi.json` unchanged; a request
  under a non-default preset validated with its schemas (400 / 422 `02308`); `/ui/` serves Scalar with every preset, no
  external URL
- [ ] T2 Documents per preset and their routes
- [ ] T3 Scalar vendored and configured, Swagger UI removed
- [ ] T4 Docs: architecture.project.md (served document, line feed note, structure), README.md, `.spec/spec-issues.md`
  (findings); findings in #205
- [ ] T5 Checks: lint-imports, unit, smoke (MTEST pending for the maintainer: `rpp` changes)

## Open questions

- none
