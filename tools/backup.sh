#!/usr/bin/env bash
#
# backup.sh
#
# a quick manual backup script using 7zip
#

set -euo pipefail

cd "$(dirname "${0}")/.."

HERE="$(basename -- "$(realpath .)")"
ZIPFILE="../${HERE}-$(date '+%Y%m%dT%H%M%S')-$(hostname).zip"

Zz=$(which 7z)

(
set -x

"${Zz}" a -spf -bb1 -bt -stl -snl -tzip "${ZIPFILE}" \
    ./build \
    ./.circleci \
    ./.coveragerc \
    ./coverlovin2 \
    ./coverlovin2.notes \
    ./coverlovin2.py \
    ./.gitignore \
    ./LICENSE.TXT \
    ./Notes.md \
    ./Pipfile \
    ./Pipfile.lock \
    ./pyproject.toml \
    ./README.md \
    ./setup.py \
    ./tools \
    ./.travis.yml \

"${Zz}" l "${ZIPFILE}"
)

echo -e "\n\n\n"

ls -lh "${ZIPFILE}"
