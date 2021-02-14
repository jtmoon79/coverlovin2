#!/usr/bin/env bash

set -e
set -u

cd "$(dirname -- "${0}")/.."

set -x
exec yamllint --strict --config-file ./tools/yamllint.yml ./.circleci/
