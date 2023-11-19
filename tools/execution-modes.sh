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
    # execute as a developer
    "${PYTHON}" ./coverlovin2/app.py --version
)
(
    # execute module outside of project directory
    cd ~
    coverlovin2=$(which coverlovin2)
    set -x
    python -m coverlovin2 --version
    # execute as a standalone program
    "${coverlovin2}" --version
    # execute as a pip-run remote module
    # requires system program `git`, Python program `pip-run`
    pip-run --use-pep517 --quiet \
      "git+https://github.com/jtmoon79/coverlovin2" \
      -- -m coverlovin2 --version
)
