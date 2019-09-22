#!/usr/bin/env bash

set -e
set -u
set -o pipefail

cd "$(dirname -- "${0}")/.."

# `gfmtoc` should be installed by a prior `pipenv install --dev`
gfmtoc ./README.md
