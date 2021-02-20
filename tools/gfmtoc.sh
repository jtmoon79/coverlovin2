#!/usr/bin/env bash

set -e
set -u

cd "$(dirname -- "${0}")/.."

# `gfmtoc` should be installed by a prior `pipenv install --dev`
set -x
exec gfmtoc "${@}" ./README.md
