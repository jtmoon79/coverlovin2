#!/usr/bin/env bash
#
# uninstall, build, install, run
#
# presumes python in $PATH is expected (this should be run in a virtual env)

set -euo pipefail

cd "$(dirname -- "${0}")/.."

if ! python -B ./tools/is_venv.py &>/dev/null; then
    echo "ERROR: $(basename -- "${0}") must be run in a python virtual environment" >&2
    exit 1
fi

(
    set -x
    python --version
    python -m pip --version
    python -m pip list -vvv
)

# uninstall any previous install (must be done outside the project directory)
(
    cd ..
    set -x
    python -m pip uninstall \
        --verbose --disable-pip-version-check --no-python-version-warning \
        --yes coverlovin2
)
# remove previous build artifacts
rm -rfv ./dist/ ./CoverLovin2.egg-info/

# does coverlovin2 run when not formally installed?
(
    set -eux
    python coverlovin2/app.py --version
)

# build using wheels
version=$(python -B -c 'from coverlovin2 import app as ca;print(ca.__version__, end="")')
(
    set -x
    python setup.py bdist_wheel
)
# note the contents of dist
(
    set -x
    ls -l ./dist/
)
# get the full path to the wheel file
# (usually, `basename $PWD` is 'coverlovin2' but on circleci it's 'project')
cv_whl=$(readlink -f -- "./dist/CoverLovin2-${version}-py3-none-any.whl")
if ! [[ -f "${cv_whl}" ]]; then
    cv_whl=$(readlink -f -- "./dist/CoverLovin2-${version}-py3.7-none-any.whl")
fi

# install the wheel (must be done outside the project directory)
(
    cd ..
    set -x
    python -m pip install --verbose --debug "${cv_whl}"
)

# make sure to attempt uninstall if asked
uninstall=false
if [[ "${1-}" == "--uninstall" ]]; then
    uninstall=true
fi

function exit_() {
    if ${uninstall}; then
        (
            set -x
            python -m pip uninstall -v --yes "coverlovin2"
        )
    else
        echo "Skip uninstall" >&2
    fi
}
trap exit_ EXIT

# does it run?
(
    set -eux
    python coverlovin2/app.py --version
)
(
    cd ~
    set -eux
    which coverlovin2
    coverlovin2 --version
    python -m coverlovin2 --version
)
