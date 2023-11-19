#!/usr/bin/env bash

set -e
set -u

cd "$(dirname -- "${0}")/.."

if ! [[ "${PYTHON+x}" ]]; then
    PYTHON='python'
fi
readonly COVERAGE_RC='./.coveragerc'

set -x
exec \
    "${PYTHON}" -m pytest -vv \
    --full-trace --showlocals \
    --cov-config="${COVERAGE_RC}" \
    --cov-report=xml \
    "${@}" \
    ./coverlovin2/
