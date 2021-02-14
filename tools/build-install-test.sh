#!/usr/bin/env bash
#
# uninstall, build, install, run
#
# presumes python in $PATH is expected (this should be run in a virtual env)

set -e
set -u
set -o pipefail

cd "$(dirname -- "${0}")/.."

if ! python -B ./tools/is_venv.py &>/dev/null; then
    echo "ERROR: $(basename -- "${0}") must be run in a python virtual environment"
    exit 1
fi

set -x
# uninstall any previous install (must be done outside the project directory)
cd ..
python -m pip uninstall --yes coverlovin2
# remove previous build artifacts
rm -rfv ./dist/ ./CoverLovin2.egg-info/

# build using wheels
cd -
version=$(python -B -c 'from coverlovin2 import coverlovin2 as c2;print(c2.__version__)')
python setup.py bdist_wheel
# note the contents of dist
ls -l ./dist/
# get the full path to the wheel file
# (usually, `basename $PWD` is 'coverlovin2' but on circleci it's 'project')
cv_whl=$(readlink -f -- "./dist/CoverLovin2-${version}-py3-none-any.whl")
if ! [ -f "${cv_whl}" ]; then
    cv_whl=$(readlink -f -- "./dist/CoverLovin2-${version}-py3.7-none-any.whl")
fi

# install the wheel (must be done outside the project directory)
cd ..
python -m pip install "${cv_whl}"

# make sure to attempt uninstall if asked
uninstall=false
if [ "${1+x}" == '--uninstall' ]; then
    uninstall=true
fi
function on_exit(){
    if ${uninstall}; then
        python -m pip uninstall "coverlovin2"
    fi
}
trap on_exit EXIT

# does it run?
coverlovin2 --version

if ${uninstall}; then
    # and test uninstall if asked
    python -m pip uninstall "coverlovin2"
    # if script got here then no need to run uninstall on EXIT
    uninstall=false
fi
