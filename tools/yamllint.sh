#!/usr/bin/env bash

set -e
set -u

cd "$(dirname -- "${0}")/.."

yamllint --strict --config-file ./tools/yamllint.yml ./.circleci/
