# The deployment image of the proxy (#184): one image for every instance, which differ only in the configuration
# mounted at /config/config.yaml. Hardened: a non-root user, nothing writable but /data and the tmpfs the deployment
# mounts, no pip or package manager in the final stage. .docker/Dockerfile stays the development image.
#
# Build from the repository root:  docker build -f deploy/docker/Dockerfile -t rpp-proxy .
#
# The base is pinned by the digest of its multi-architecture index (python:3.11-slim-bookworm, the version the project
# is tested with). Renew it with: docker buildx imagetools inspect python:3.11-slim-bookworm
ARG PYTHON_IMAGE=python:3.11-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39

FROM ${PYTHON_IMAGE} AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install -r /tmp/requirements.txt
# The packages only the tests need, and pip itself, are not part of the image.
RUN /opt/venv/bin/pip uninstall -y pytest pytest-xdist execnet iniconfig pluggy \
    && /opt/venv/bin/pip uninstall -y pip setuptools
COPY src /app
# The root file system is read-only at run time: compile the bytecode now.
RUN find /app -name __pycache__ -prune -exec rm -rf {} + \
    && python -m compileall -q /app /opt/venv

FROM ${PYTHON_IMAGE}
# No pip, no setuptools and no ensurepip in the final stage: nothing installs at run time.
RUN rm -rf /usr/local/lib/python3.11/site-packages/pip* /usr/local/lib/python3.11/site-packages/setuptools* \
           /usr/local/lib/python3.11/ensurepip /usr/local/bin/pip* \
    && groupadd --system --gid 10001 rpp \
    && useradd --system --uid 10001 --gid rpp --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin rpp \
    && mkdir -p /config /data \
    && chown rpp:rpp /data
COPY --from=build /opt/venv /opt/venv
COPY --from=build /app /app

WORKDIR /app
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RPP_CONFIG_FILE=/config/config.yaml \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    WEB_CONCURRENCY=3 \
    FORWARDED_ALLOW_IPS=127.0.0.1 \
    UVICORN_TIMEOUT_WORKER_HEALTHCHECK=60

USER 10001:10001
EXPOSE 8000

# The discovery document needs no authentication, but an RPP-Cltrid; it answers 500 when the configuration lacks its
# keys. Starting takes a while: every worker builds the app from openapi.yaml, which on a busy host of two CPUs took
# minutes (#195). During the start period a check runs every 5 s, so a container is healthy soon after it is up.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --start-interval=5s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request as u; u.urlopen(u.Request('http://127.0.0.1:%s/.well-known/rpp' % os.environ['UVICORN_PORT'], headers={'RPP-Cltrid': 'healthcheck', 'Accept': 'application/rpp+json'}), timeout=4)"]

# uvicorn takes its host, port, workers (WEB_CONCURRENCY) and the proxies it trusts for X-Forwarded-* from the
# environment, so a deployment sets them without another command line. A worker that does not answer the parent's ping
# within UVICORN_TIMEOUT_WORKER_HEALTHCHECK seconds is restarted; uvicorn's 5 s killed workers still building the app
# on a busy host, over and over (#195).
CMD ["uvicorn", "--proxy-headers", "--no-server-header", "main:app"]
