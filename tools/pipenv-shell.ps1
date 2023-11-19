#!powershell
#
# start this project's pipenv shell with decorated window title

$ErrorActionPreference = "Stop"
$DebugPreference = "Continue"
Set-PSDebug -Trace 2
Push-Location $PSScriptRoot
$title_original = $Host.UI.RawUI.WindowTitle

try {
    if (-not (Get-Variable 'Python' -Scope 'Global' -ErrorAction 'Ignore')) {
        if ([Environment]::GetEnvironmentVariable('Python'))
        {
            $Python = $env:Python
        }
    }
    if (-not (Get-Variable 'Python' -Scope 'Global' -ErrorAction 'Ignore')) {
        $Python = Get-Command -Name "python.exe"
    }

    # update the shell window title with information about the virtual environment
    & $Python --version
    if (-not $?) {
        throw "ERROR: command failed: $Python --version"
    }
    $venv_loc = & $Python -m pipenv --venv
    if (-not $?) {
        throw "ERROR: command failed: $Python -m pipenv --venv"
    }
    $Host.UI.RawUI.WindowTitle = $Host.UI.RawUI.WindowTitle + "`npipenv: $venv_loc ($py_ver)"

    # run `pipenv shell` command
    Write-Debug "$Python -m pipenv shell`n"
    & $Python -m pipenv shell $args
} finally {
    Write-Debug "Exiting script $PSCommandPath"
    Pop-Location
    # restore the window title
    $Host.UI.RawUI.WindowTitle = $title_original
    # XXX: presuming these were the prior settings
    $DebugPreference = "SilentlyContinue"
    Set-PSDebug -Trace 0
}
