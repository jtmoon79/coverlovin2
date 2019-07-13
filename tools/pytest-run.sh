#!/usr/bin/env bash

set -e
set -u

cd "$(dirname -- "${0}")/.."
readonly COVERAGE_RC='./.coveragerc'
pytest -vv \
    --full-trace --showlocals \
    --cov-config="${COVERAGE_RC}" \
    --cov-report=xml \
    ./coverlovin2/
