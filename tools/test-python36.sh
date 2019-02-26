#!/usr/bin/env bash

set -e
set -u
set -o pipefail

cd "$(dirname -- "${0}")/.."

if ! python --version | grep -qFe ' 3.6'; then
    echo 'ERROR: wrong python version' "$(python --version)" >&2
    exit 1
fi

# this should fail to run
if ! python coverlovin2/coverlovin2.py --version &>/dev/null; then
    exit 0
fi
echo 'ERROR: python version' "$(python --version)" 'should not have run successfully' >&2
exit 1
