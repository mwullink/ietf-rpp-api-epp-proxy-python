#!/bin/sh
# Installs requirements-dev.txt and runs the tests marked `pyversions` on every supported Python, each in a
# python:<version>-slim container (no compiler: a dependency without a wheel for that Python fails to install).
# Usage: ./test_python_versions.sh [version ...]    (default: every supported version)
# The supported versions are those of https://devguide.python.org/versions/ in bugfix or security status.
set -e
cd "$(dirname "$0")"

VERSIONS=${*:-"3.11 3.12 3.13 3.14 3.15"}

# The build context is sent as a tar, so it works from a devcontainer that uses the host's Docker. It holds the files
# git tracks or would track under the paths the tests need, never ignored ones (.env, *.local.yaml).
context=$(mktemp -d)
trap 'rm -rf "$context"' EXIT
cat > "$context/Dockerfile" <<'EOF'
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim
WORKDIR /proxy
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_ROOT_USER_ACTION=ignore
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
ENTRYPOINT ["python", "-m", "pytest", "-p", "no:cacheprovider", "-m", "pyversions"]
EOF

# Only the files that hold a marked test are collected: collecting every unit test needs files outside the context.
tests=$(grep -l '@pytest.mark.pyversions' tests/unit/*.py)

failed=""
for version in $VERSIONS; do
    echo "=== Python $version"
    image="rpp-proxy-pyversions:$version"
    if ! git ls-files -z -co --exclude-standard -- pyproject.toml requirements.txt requirements-dev.txt src tests 'config*.yaml' \
        | tar -c --null -T - -C "$context" Dockerfile \
        | docker build --progress=plain --build-arg "PYTHON_VERSION=$version" -t "$image" - >"$context/build.log" 2>&1; then
        tail -n 40 "$context/build.log"
        echo "=== Python $version: FAILED to install"
        failed="$failed $version"
    elif docker run --rm "$image" $tests; then
        echo "=== Python $version: passed"
    else
        echo "=== Python $version: FAILED"
        failed="$failed $version"
    fi
done

if [ -n "$failed" ]; then
    echo "Failed on:$failed"
    exit 1
fi
echo "Passed on: $VERSIONS"
