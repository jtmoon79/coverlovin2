#!/usr/bin/env bash
#
# start pipenv shell with decorated prompt

set -e
set -u
set -o pipefail

cd "$(dirname -- "${0}")/.."

# get path to pipenv installed with local python 3.7 installation
ver='3.7'
python=$(py -${ver} -c "import sys;import os;print(os.path.abspath(sys.executable));")
pipenv=$(py -${ver} -c "import sys;import os;print(os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pipenv'));")
venv=$("${pipenv}" --venv)
pyver=$(python --version)

# update the prompt with information about the virtual environment
export PS1="pipenv: ${venv} (${pyver})
${PS1+x}"
eval "$(pipenv --completion)"

# run `pipenv shell` command
# BUG: the exported `PS1` is not used by the shell spawned by `pipenv shell`
#bash --rcfile <(cat ~/.bashrc; echo 'export PS1="${PS1} foo\n"'; "${pipenv}" shell)
"${pipenv}" shell --fancy
