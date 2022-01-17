#!/usr/bin/env bash
#
# run coverlovin2 in all possible execution manners

set -euo pipefail

if ! [[ "${PYTHON+x}" ]]; then
    PYTHON="python"
fi

cd "$(dirname -- "${0}")/.."

(
    set -x
    "${PYTHON}" ./coverlovin2/app.py --version
)
(
    cd ~
    set -x
    python -m coverlovin2 --version
    "$(which coverlovin2)" --version
)
