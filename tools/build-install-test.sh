#!/usr/bin/env bash
#
# uninstall, build, install, run
#
# presumes python in $PATH is expected (this should be run in a virtual env)

set -e
set -u

cd "$(dirname -- "${0}")/.."

if ! python -B ./tools/is_venv.py &>/dev/null; then
    echo "ERROR: $(basename -- "${0}") must be run in a python virtual environment"
    exit 1
fi


set -x
# uninstall any previous install (must be done outside the project directory)
cd ..
python -m pip uninstall --yes coverlovin2

# build using wheels
cd -
version=$(python -B -c 'from coverlovin2 import coverlovin2 as c2;print(c2.__version__)')
python setup.py bdist_wheel

# install the wheel (must be done outside the project directory)
cd ..
python -m pip install "./coverlovin2/dist/CoverLovin2-${version}-py3-none-any.whl"

# does it run?
coverlovin2 --version
