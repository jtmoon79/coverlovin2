#!/usr/bin/env bash
#
# helper script to validate CircleCI YAML configuration

if ! which circleci &>/dev/null; then
    echo "ERROR cannot find 'circleci' in the PATH" >&2
    echo >&2
    echo "See https://circleci.com/docs/local-cli/" >&2
    exit 1
fi

cd "$(dirname "${0}")/../.circleci"
set -x
exec circleci config validate ./config.yml
