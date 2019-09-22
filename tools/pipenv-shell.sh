#!/usr/bin/env bash
#
# start this project's pipenv shell with decorated prompt

set -e
set -u
set -o pipefail

cd "$(dirname -- "${0}")/.."

# get path to pipenv installed with local python 3.7 installation
ver='3.7'
python='python'
pipenv='pipenv'

# attempt to get specific version of python and pipenv
if which py &>/dev/null; then
    # Windows only
    python=$(py -${ver} -c "import sys;import os;print(os.path.abspath(sys.executable));")
    pipenv=$(py -${ver} -c "import sys;import os;print(os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pipenv'));")
elif which "python${ver}" &>/dev/null; then
    python=$(which "python${ver}")
    pipenv=$(which "pip${ver}")
elif which python3 &>/dev/null; then
    python=$(which python3)
    pipenv=$(which pip3)
fi

echo "${python}"
"${python}" --version
echo "${pipenv}"
"${pipenv}" --version

pyver=$("${python}" --version)
venv=$("${pipenv}" --venv)

# update the prompt with information about the virtual environment
export PS1="pipenv: ${venv} (${pyver})
${PS1+x}"
eval "$("${pipenv}" --completion)"

# run `pipenv shell` command
# BUG: the exported `PS1` is not used by the shell spawned by `pipenv shell`
#bash --rcfile <(cat ~/.bashrc; echo 'export PS1="${PS1} foo\n"'; "${pipenv}" shell)
set -x
"${pipenv}" shell --fancy
