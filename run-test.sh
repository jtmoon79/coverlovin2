#!/usr/bin/env bash
#
# for Travis CI runs
#
# this will modify the system is not recommended to be run on a development
# host.

set -e
set -u
set -x

cd "$(dirname -- "${0}")"

python='false'
if which python3.7 &>/dev/null; then
    python='python3.7'
elif which python3 &>/dev/null; then
    python='python3'
elif which py &>/dev/null; then
    python=$(py -3.7 -c "import sys;import os;print(os.path.abspath(sys.executable));")
else
    echo "ERROR: unable to find suitable python" >&2
    exit 1
fi

"${python}" --version  # record version

if ! "${python}" -m pip --version; then
    echo "ERROR: pip is not installed" >&2
    exit 1
fi
if ! which pipenv &>/dev/null; then
    "${python}" -m pip install pipenv
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
# create and install distributable with pip
#
# upgrade installer libraries
#"${python}" -m pip install --user --upgrade setuptools wheel
# create the install package
#"${python}" ./setup.py sdist
"${python}" setup.py bdist_wheel
DIST_WHL="./dist/CoverLovin2-*-py3-none-any.whl"
"${python}" -m pip install "${DIST_WHL}"

cd ..
coverlovin2 --help
