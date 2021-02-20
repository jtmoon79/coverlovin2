#!/usr/bin/env bash

set -e
set -u

cd "$(dirname -- "${0}")/.."

set -x
exec \
  yamllint \
    --config-file ./tools/yamllint.yml \
    "${@}" \
    ./tools/yamllint.yml ./.travis.yml ./.circleci/
