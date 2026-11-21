# Configurations

The configurations of the proxy, composed of layers (#217). An environment is what `RPP_CONFIG_FILE` names; without it
the proxy reads `environments/epp-docker.yaml`.

| Directory | Holds | Example |
|---|---|---|
| `protocols/` | How the proxy speaks to a registry: `rpp_backend` and the protocol's client settings | `rri.yaml`: port 51131, TLS |
| `backends/` | What one registry server holds: its profile and presets, LGRs, TLDs; includes its protocol | `rri.yaml`: DENIC |
| `environments/` | One deployment of a backend: host, TLS verification, discovery; includes `common.yaml` and its backend | `rri-mtest.yaml` |
| `common.yaml` | What every test deployment shares: the default signalling, the discovery placeholders, and every path of `rpp_protocol_config` as null | |

`rpp_protocol_config` is what the registry does where its protocol leaves the choice to the server: authInfo rules,
contact limits, transition periods. The proxy does not use it; the integration suite selects its cases and times its
waits by it ([testing.project.md](../docs/agents/testing.project.md#selectors)). Each layer states what it knows: the
protocol what its specification fixes (for RRI, DENIC's rules), the backend its server's policy and periods, the
environment what is its own. A test environment descriptor keeps only a server's defects (`facts.bugs`).

A file may start with `include: [<path>, ...]` (relative to the file). A file resolves to its includes in order, then
itself, then the untracked `<name>.local.yaml` next to it (`*.local.yaml` is in `.gitignore`), so any layer can be
changed on one machine without a change to the tracked file. A mapping merges key by key; a list or a value replaces;
a top-level `null` unsets a key. The loader is [src/settings/layered_yaml.py](../src/settings/layered_yaml.py).

For example, to point the MTEST environment at a local RRI server, `environments/rri-mtest.local.yaml`:

```yaml
rpp_rri_host: 172.17.0.9
rpp_rri_tls_insecure_skip_verify: true
```

A key the proxy does not know is ignored; one that starts with `rpp_` is logged as a warning with the file it is in.
