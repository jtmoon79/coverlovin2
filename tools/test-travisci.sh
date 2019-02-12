#!/usr/bin/env bash
#
# for Travis CI runs
#
# this will modify the system is not recommended to be run on a development
# host.

set -e
set -u
set -x

cd "$(dirname -- "${0}")/.."

python --version  # record version
python -B ./tools/is_venv.py  # check if virtual env, script will exit if not

if ! python -m pip --version; then
    echo "ERROR: pip is not installed" >&2
    exit 1
fi
if ! which pipenv &>/dev/null; then
    python -m pip install pipenv
fi
pipenv --version  # record version
pipenv install --dev
echo
echo

#
# run pytest with codecov tool, upload the report
#

readonly COVERAGE_XML='coverage.xml'
readonly COVERAGE_RC='./.coveragerc'
export COVERAGE_PROCESS_START=$(readlink -f -- "${COVERAGE_RC}")
coverage --version  # record version
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
coverage xml "--rcfile=${COVERAGE_RC}" -o "${COVERAGE_XML}"
coverage report
# upload to codecov.io
codecov --file "${COVERAGE_XML}" 


#
# create and install distributable with pip, test it can print --help
#
# upgrade installer libraries first
python -m pip install --upgrade setuptools wheel
./tools/build-install-test.sh