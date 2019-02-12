#!/usr/bin/env bash
#
# for Travis CI runs

set -e
set -u
set -x

cd "$(dirname -- "${0}")"

py='false'
if which python3 &>/dev/null; then
    py='python3'
elif which python3.7 &>/dev/null; then
    py='python3.7'
elif which py &>/dev/null; then
    py='py -3.7'
fi

${py} -m pip install pipenv
pipenv install --dev
echo
echo

#
# run pytest with codecov tool
#

export COVERAGE_PROCESS_START=$(readlink -f -- '.coveragerc')

COVERAGE_XML='coverage.xml'
COVERAGE_RC='./.coveragerc'
coverage erase

# XXX: several methods of invoking codecov, the uncommented method is the only
#      one that works
#
# method 1:
# pass codecov flag --cov, see https://github.com/codecov/example-python#pytest
#pytest -v --cov=./ ./coverlovin2/test/
#
# method 2:
#coverage run --source=coverlovin2 -m pytest ./coverlovin2/test/
#
# method 3:
# call codecov at the end, see https://github.com/codecov/example-python#overview
coverage run "--rcfile=${COVERAGE_RC}" -m pytest ./coverlovin2/test/
coverage xml "--rcfile=${COVERAGE_RC}"
codecov --file "${COVERAGE_XML}"
coverage report
