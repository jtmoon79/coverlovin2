#!/usr/bin/env bash
#
# runs a series of coverlovin2 runs.
# Reads the file passed as argument to this script.  For each line in that file,
# pass the entire line as arguments to coverlovin2.
#

set -e
set -u
set -o pipefail

coverlovin="./coverlovin2/app.py"
runs_input=${1:-$(realpath -- "$(dirname -- "${0}")")/runs.local.example}

(set -x
python --version
)
sleep 0.5

cd "$(dirname -- "${0}")/.."

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
