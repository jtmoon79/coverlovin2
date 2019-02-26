#!/usr/bin/env bash
#
# start pipenv shell with decorated prompt

set -e
set -u
set -o pipefail

cd "$(dirname -- "${0}")"

# get path to pipenv installed with local python 3.7 installation
ver='3.7'
python=$(py -${ver} -c "import sys;import os;print(os.path.abspath(sys.executable));")
pipenv=$(py -${ver} -c "import sys;import os;print(os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pipenv'));")
venv=$("${pipenv}" --venv)
pyver=$(python --version)

# update the prompt with information about the virtual environment
# XXX: no access to PS1 from here, secondly the exported `PS1` is not used by
#      the new instance of `pipenv shell` run below 
export PS1="pipenv: ${venv} (${pyver})
${PS1+x}"

# run `pipenv shell` command
"${pipenv}" shell
