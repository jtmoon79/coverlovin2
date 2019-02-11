#!/usr/bin/env bash

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
#python3 -m pipenv install --dev
pipenv install --dev
echo
echo

#
# run pytest with codecov tool
#

export COVERAGE_PROCESS_START=$(readlink -f -- '.coveragerc')

COVERAGE_XML='coverage.xml'
COVERAGE_RC='./.coveragerc'
# XXX: several methods of invoking codecov, the uncommented method is the only
#      one that works

# method 1:
# pass codecov flag --cov, see https://github.com/codecov/example-python#pytest
#pytest -v --cov=./ ./coverlovin2/test/

# method 2:
#coverage run --source=coverlovin2 -m pytest ./coverlovin2/test/

# method 3:
# call codecov at the end, see https://github.com/codecov/example-python#overview
coverage erase
coverage run "--rcfile=${COVERAGE_RC}" -m pytest ./coverlovin2/test/
coverage xml -o "${COVERAGE_XML}"

# check env vars if we are running in Travis CI, if yes then add info to report 
# see https://docs.travis-ci.com/user/environment-variables/#default-environment-variables
#
# XXX: may not need to manually add Travis CI info, coverage claims to
#      "provided automatically for supported CI companies"
cov_ex=
#if [ "${TRAVIS+x}" ] ; then
#    cov_ex="--build ${TRAVIS_BUILD_NUMBER}"
#fi
# XXX: REMOVE WHEN PUBLIC: just remove the --token part
codecov --token=e799d848-b9ab-40a5-bfa1-ce171f916368 ${cov_ex} --file "${COVERAGE_XML}"
coverage report
