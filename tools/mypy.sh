#!/usr/bin/env bash

set -e
set -u

cd "$(dirname -- "${0}")/.."

set -x
exec \
  python -m mypy \
    --config-file ./mypy.ini \
    "${@}" \
    ./coverlovin2/app.py
