#!/usr/bin/env bash
#
# runs a series of coverlovin2 runs.
# Reads the file passed as argument to this script.  For each line in that file,
# pass the entire line as arguments to coverlovin2.
#

set -e
set -u
set -o pipefail

coverlovin="$(dirname -- "${0}")/../app.py"

which python
python --version
sleep 0.5

runs_input=${1:-$(dirname -- "${0}")/runs.local.example}

while read line; do
    if [[ -z "${line}" ]] || [[ '#' = "${line:0:1}" ]]; then
        continue
    fi
    (
        set -x 
        eval python "${coverlovin}" ${line}
    )
    echo
done < "${runs_input}"
