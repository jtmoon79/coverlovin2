#!powershell
#
# run coverlovin2 in all possible execution manners

$PYTHON = "python.exe"
if ($env:PYTHON -ne $null) {
    $PYTHON = $env:PYTHON
}

$ErrorActionPreference = "Stop"
$DebugPreference = "Continue"
Push-Location "$PSScriptRoot/.."
Set-PSDebug -Trace 1

try {
    & $PYTHON --version

    # execute as a developer
    & $PYTHON coverlovin2/app.py --version $args

    # execute module outside of project directory
    cd ~
    & $PYTHON -m coverlovin2 --version $args

    # execute as a standalone program
    $coverlovin2_exe = Get-Command "coverlovin2.exe"
    Write-Debug "${coverlovin2_exe}.Source --version $args"
    & $coverlovin2_exe.source --version $args

    # requires system program `git`, Python program `pip-run`
    #pip-run --use-pep517 --quiet `
    #  "git+https://github.com/jtmoon79/coverlovin2@feature/runpy-invoke" `
    #  -- -m coverlovin2 --version

    Pop-Location
} finally {
    # XXX: presuming these were the prior settings
    Set-PSDebug -Trace 0
    Pop-Location
    $DebugPreference = "SilentlyContinue"
}
