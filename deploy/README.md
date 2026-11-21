# Deployment on Ubuntu with Ansible

Deploys the proxy as containers on an Ubuntu host (22.04 or later):

- an unprivileged user (`rpp`) owns a **rootless Docker** daemon and every container of the deployment;
- one **hardened image** ([docker/Dockerfile](docker/Dockerfile)), built on the host from a commit of this repository;
- **one instance per configuration**, each a container with its own port and 3 uvicorn workers;
- the **EPP test server** ([EPP-server-docker](https://github.com/pawel-kow/EPP-server-docker)), internal only, as
  the backend of the `epp` instance;
- **TLS is terminated outside**, by an nginx container on the host's root Docker daemon.

```
                    root Docker                               rootless Docker (user rpp)
 client ──TLS──▶  nginx container ──http──▶ 172.17.0.1:8091 ──▶ rpp-proxy-epp ──▶ epp-server:743 (network rpp-epp)
                                   └─────▶ 172.17.0.1:8092 ──▶ rpp-proxy-sqlite-demo ──▶ /data/demo.db
                                   └─────▶ 172.17.0.1:8093 ──▶ rpp-proxy-rri-mtest ──TLS──▶ rri.test.denic.de:51131
```

The two daemons share no network. The instances publish their ports on the gateway of the root daemon's default
bridge (`docker0`, usually `172.17.0.1`). nginx reaches that address as `host.docker.internal`, and nothing outside
the host can reach it.

## Layout

| Path | What |
|---|---|
| [docker/Dockerfile](docker/Dockerfile) | The image: non-root UID 10001, read-only root, no pip, healthcheck on `/.well-known/rpp` |
| [ansible/site.yml](ansible/site.yml) | The playbook: roles `rootless_docker`, `epp_server`, `rpp_proxy` |
| [ansible/configs/](ansible/configs/) | The configuration templates of the instances, one per repository environment |
| [ansible/inventory/example/](ansible/inventory/example/) | An inventory to copy: host, instances, vault |
| `ansible/roles/*/defaults/main.yml` | Every setting, with its default and meaning |

On the host, under `/home/rpp`:

| Path | What |
|---|---|
| `rpp-proxy/src/` | The checkout the image is built from (`rpp-proxy:<commit>`) |
| `rpp-proxy/docker-compose.yml` | One service per instance, generated |
| `rpp-proxy/instances/<name>/config/config.yaml` | The configuration of an instance, readable only by the container's user |
| `rpp-proxy/instances/<name>/data/` | The data of an instance with `data: true` (its SQLite file) |
| `epp-server-docker/`, `epp-server.env`, `epp-server.compose.yml` | The EPP test server, its settings and the override that removes its ports |

## Prerequisites

On the machine you run Ansible from:

```bash
python -m venv ~/.venvs/ansible && . ~/.venvs/ansible/bin/activate
pip install ansible-core            # 2.15 or later; ansible-lint to check changes
cd deploy/ansible && ansible-galaxy collection install -r requirements.yml
```

On the target host you need SSH access as a user with sudo, Python 3, and the root Docker daemon of nginx
**running**. The playbook takes the bind address from `docker0` unless you set `rpp_proxy_bind_address`. If Docker
isn't installed yet, the playbook installs Docker CE, which also starts the root daemon.

## Deploying

`ansible.cfg` names no inventory: name it with `-i`, or with `ANSIBLE_INVENTORY`, which overrides `ansible.cfg`. A run
that names none targets no host.

Run the checks first. They change nothing on the host, and print what the role found and what it will do:

```bash
ansible-playbook -i inventory/prod/hosts.yml site.yml --tags preflight --ask-vault-pass --ask-become-pass
```

The summary lists:
- the Docker packages and the repository definitions;
- the root daemon;
- the rootless daemons of all users;
- what happens to the deployment user and its `daemon.json`;
- the AppArmor profile.

The run stops if Ubuntu's `docker.io` is installed, or if a port of an instance is in use by a program other than the
deployment user's daemon. The role changes only the deployment user's own daemon:
- **Packages:** it installs only what is missing, and never upgrades. It adds the Docker CE repository only to a host
  that has no definition of it.
- **The deployment user's daemon:** if the user already has a rootless daemon whose `daemon.json` the role didn't
  write, the role uses it as it is, with no new configuration and no restart. The role leaves a marker file
  `.managed-by-rpp-deploy` beside a `daemon.json` it wrote.
- **AppArmor:** it writes `/etc/apparmor.d/usr.bin.rootlesskit` only when no profile there or elsewhere already covers
  rootlesskit, or when the role wrote the one there.
- **Other users' rootless daemons:** it reads them, and never changes them.

Then deploy:

```bash
cd deploy/ansible
cp -r inventory/example inventory/prod                    # inventory/* other than example is ignored by git
$EDITOR inventory/prod/hosts.yml                          # the host
$EDITOR inventory/prod/group_vars/rpp_hosts/main.yml      # versions, instances, base URLs
cp inventory/prod/group_vars/rpp_hosts/vault.yml.example inventory/prod/group_vars/rpp_hosts/vault.yml
$EDITOR inventory/prod/group_vars/rpp_hosts/vault.yml     # the database password, the SQLite client hashes
ansible-vault encrypt inventory/prod/group_vars/rpp_hosts/vault.yml
ansible-playbook -i inventory/prod/hosts.yml site.yml --ask-vault-pass
```

### An inventory in its own repository

`inventory/<name>/` is ignored by git, so nothing keeps it. To keep it under version control, give it its own (private)
repository: `hosts.yml` and `group_vars/` with the encrypted vault. Its instances use the repository's templates through
`playbook_dir` (see [Instances](#instances)), so it holds no copy of them, and a template of its own only for a
configuration the repository has none of. Run the playbook of this repository with it:

```bash
export ANSIBLE_INVENTORY=/path/to/the-inventory/hosts.yml   # or -i on each run
cd deploy/ansible && ansible-playbook site.yml --ask-vault-pass
```

A small script in the inventory repository that sets `ANSIBLE_INVENTORY` and runs `ansible-playbook` from
`deploy/ansible` saves typing it.

Running the playbook again does nothing unless something changed. The changes it applies:

- **A new `rpp_proxy_version`** builds a new image and recreates the instances.
- **A changed configuration** recreates its instance only, because the config's checksum is a label of the container.
- **A removed instance** has its container removed, but keeps its directory and data.

The playbook starts the instances one after the other, and waits for each to be healthy (`rpp_proxy_wait_timeout`,
300 s) before the next: every worker builds the app at start, which takes most of a CPU for a while. A host with few
CPUs or little free memory should run fewer workers (`rpp_proxy_workers`, or `workers` of an instance): three instances
of three workers on two CPUs took minutes to start (#195). After a reboot the daemon starts every instance at once;
uvicorn then waits up to 60 s for a worker to answer (`UVICORN_TIMEOUT_WORKER_HEALTHCHECK`), and the healthcheck allows
180 s to start.

Pin `rpp_proxy_version` and `epp_server_version` to commits for repeatable deployments.

A SQLite client hash comes from the repository's own tool, which reads the password from standard input:

```bash
cd src && ../.venv/bin/python -m registry_adapter.sqlite.hash_password
```

## Instances

`rpp_proxy_instances` lists the instances, and nothing else in the roles names them. **To add an instance, add an
entry** with a config template: one of the repository's in [ansible/configs/](ansible/configs/), or the inventory's own.

```yaml
rpp_proxy_instances:
  - name: epp-second            # [a-z0-9-], unique: the service and directory name
    port: 8094                  # unique, 1024 or above
    config_template: "{{ playbook_dir }}/configs/epp.yaml.j2"  # sees this entry as `instance`
    epp_network: true           # joins the EPP test server's network
    base_url: https://rpp-epp-second.example.net  # any further key is free for the template
```

The entry keys are:

| Key | Meaning |
|---|---|
| `name`, `port` | Required |
| `config_template` or `config` | Exactly one: a Jinja2 template of the proxy's `config.yaml` (absolute, or relative to the inventory), or the configuration as a YAML mapping |
| `data` | `true` mounts `instances/<name>/data` at `/data`, for `rpp_sqlite_url: sqlite:////data/<file>.db` |
| `epp_network` | `true` attaches the instance to `rpp-epp`, where the EPP test server is `epp-server:743` |
| `workers`, `mem_limit`, `cpus`, `pids_limit`, `tmpfs_size` | Override the defaults (3, `1g`, 2, 256, `64m`) |
| `environment` | Further environment variables of the container |

Then add a `location` (or `server`) for the new port in nginx.

The example has three instances:

| Instance | Port | Configuration | Backend |
|---|---|---|---|
| `epp` | 8091 | [configs/epp.yaml.j2](ansible/configs/epp.yaml.j2) | The EPP test server, internal. Registrars `foo`/`bar` and `baz`/`qux`, as provisioned by EPP-server-docker |
| `sqlite-demo` | 8092 | [configs/sqlite-demo.yaml.j2](ansible/configs/sqlite-demo.yaml.j2) | SQLite in `/data/demo.db`; clients from the vault |
| `rri-mtest` | 8093 | [configs/rri-mtest.yaml.j2](ansible/configs/rri-mtest.yaml.j2) | DENIC RRI MTEST |

The `rri-mtest` instance passes HTTP Basic through as the RRI LOGIN, so the deployment holds no DENIC credentials.
MTEST only admits the host's public address once DENIC has put it on the RegAcc's allowlist. RRI locks a user for an
hour after 10 failed logins, and anyone who can reach the instance can trigger that
([security.project.md](../docs/agents/security.project.md)).

### SQLite with several workers

The workers of an instance share its database file. The file is in WAL mode, every unit of work holds the write lock
from its first read (`BEGIN IMMEDIATE`), and a worker waits up to 30 s for another worker's lock. The data directory
must be on a local file system, because WAL does not work on NFS. Two instances must not share a data directory.

## nginx

nginx runs on the root daemon. Give its container the host gateway, and proxy each name to its port:

```yaml
# docker-compose.yml of nginx
services:
  nginx:
    extra_hosts: ["host.docker.internal:host-gateway"]
```

```nginx
server {
    listen 443 ssl;
    server_name rpp-epp.example.net;            # the instance's base_url
    # ssl_certificate ...;
    location / {
        proxy_pass http://host.docker.internal:8091;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 90s;                 # a registry command can take long
    }
}
```

The proxy builds no URL from these headers: `rpp_base_url` comes from the configuration. It uses them in its access
log only, and trusts them from any peer (`rpp_proxy_forwarded_allow_ips`). Behind rootless Docker every connection
arrives from inside the daemon's network namespace, so the peer address can't tell nginx apart from anything else.

If ufw is active, the playbook allows `rpp_proxy_ufw_allow_from` (default `172.16.0.0/12`, the root daemon's
networks) to the published ports.

### nginx on the host's loopback

If nginx reaches the instances on the host's loopback instead (nginx on the host, or a container with
`network_mode: host`), publish the ports there and open no firewall rule:

```yaml
rpp_proxy_bind_address: 127.0.0.1
rpp_proxy_ufw_allow_from: []   # loopback needs no rule
```

nginx then proxies to `http://127.0.0.1:<port>`.

## Hardening

Each instance has these settings:

- `read_only` root;
- a `noexec,nosuid,nodev` tmpfs on `/tmp`;
- `cap_drop: ALL` and `no-new-privileges`;
- UID 10001, which on the host is a subordinate id of `rpp`, not `rpp` itself;
- memory, CPU and pids limits;
- log rotation (`rootless_docker_log_max_size`, `_max_file`).

The image holds no pip, no setuptools and no test packages. Its base is pinned by digest: renew it in
[docker/Dockerfile](docker/Dockerfile).

The daemon runs as `rpp`, which isn't in the `docker` group, so a container escape lands in an unprivileged user
namespace. On Ubuntu 23.10 and later, the role installs an AppArmor profile that allows rootlesskit a user namespace
(`rootless_docker_apparmor_profile`).

**Known issue:** the `epp` instance writes every EPP message it sends to its log, the login with the registrar's
password included (#14). Treat its container log as secret: `docker logs` as `rpp`, or the files under
`/home/rpp/.local/share/docker/containers/`.

## Operating

```bash
sudo -iu rpp                                   # DOCKER_HOST is set in its .bashrc
docker ps                                      # the instances and the EPP server
docker logs -f rpp-proxy-sqlite-demo-1
docker compose -f ~/rpp-proxy/docker-compose.yml restart epp
systemctl --user status docker                 # the rootless daemon
```

The services survive a reboot: the user's systemd instance starts with the host (linger), and the containers use
`restart: unless-stopped`.
