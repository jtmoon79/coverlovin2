#!/usr/bin/env bash
#
# for Travis CI runs
#
# this will modify the system is not recommended to be run on a development
# host.

set -e
set -u
set -o pipefail
set -x

cd "$(dirname -- "${0}")/.."

# log some things about this environment
uname -a
lsb_release -a || true
python --version  # record version

# for Python 3.6 fail test
if python --version | grep -Fqe '3.6.'; then
    if python -Bc 'from coverlovin2 import coverlovin2' &>/dev/null; then
        echo 'ERROR: Python 3.6 should refuse to work but it worked'
        exit 1
    fi
    echo 'Python 3.6 successfully failed' >&2
    exit 0
fi

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
#coverage run "--rcfile=${COVERAGE_RC}" -m pytest -v ./coverlovin2/test/
#
# method 4:
# call pytest with more *cov* parameters
pytest --cov=./coverlovin2/ --cov-config="${COVERAGE_RC}" --cov-report=xml

# codecov will return code 0 if it fails so make really sure the XML file exists
# see https://github.com/codecov/codecov-python/issues/191
if ! [ -f "${COVERAGE_XML}" ]; then
    echo "ERROR: coverage file does not exist '${COVERAGE_XML}'"
    exit 1
fi

# upload coverage report to codecov.io
codecov --file "${COVERAGE_XML}"

# upload coverage report to coveralls.io
set +x  # do not echo private enviroment variable
if [ "${COVERALLS_REPO_TOKEN+x}" ]; then
    COVERALLS_REPO_TOKEN=${COVERALLS_REPO_TOKEN} coveralls "--rcfile=${COVERAGE_RC}"
else
    echo "COVERALLS_REPO_TOKEN not set; skip use of coveralls.io" >&2
fi
set -x

#
# create and install distributable with pip, test it can print --help
#
# upgrade installer libraries first
python -m pip install --upgrade setuptools wheel
./tools/build-install-test.sh
