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
    & $PYTHON coverlovin2/app.py --version $args
    cd ~
    & $PYTHON -m coverlovin2 --version $args
    coverlovin2.exe --version $args
    Pop-Location
} finally {
    # XXX: presuming these were the prior settings
    Set-PSDebug -Trace 0
    Pop-Location
    $DebugPreference = "SilentlyContinue"
}
