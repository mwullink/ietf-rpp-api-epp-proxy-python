#!/bin/sh
# Generates the xsdata dataclasses of the DENIC RRI 5.0 XML schemas (docs/rri/xsd) into the RRI adapter.
# Needs xsdata[cli] in the virtualenv (requirements-dev.txt). xsdata 26 generates models in another style than the
# committed ones, which were generated with 25.7: do not commit regenerated models before #214.
set -e
cd src
xsdata generate ../docs/rri/xsd --package registry_adapter.rri.xml.generated --structure-style filenames
