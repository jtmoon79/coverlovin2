#!powershell
#
# run pytest for coverloving2 tests

$PYTHON = "python.exe"
if ($env:PYTHON -ne $null) {
    $PYTHON = $env:PYTHON
}

Set-Location $PSScriptRoot/..
$COVERAGE_RC = "./.coveragerc"
Set-PSDebug -Trace 1
& $PYTHON -m pytest -vv `
    --cov=./coverlovin2/ --cov-config=$COVERAGE_RC --cov-report=xml `
    $args
