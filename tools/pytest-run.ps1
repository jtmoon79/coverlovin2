# run pytest

cd $PSScriptRoot/..
$COVERAGE_RC='./.coveragerc'
Set-PSDebug -Trace 1
& pytest -vv --cov=./coverlovin2/ --cov-config=$COVERAGE_RC --cov-report=xml
