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
        $pyver = "3.9"
        Write-Debug ('$env:Python not set, searching for Python install' + " $pyver")
        $py = "C:\Windows\py.exe"
        Get-ChildItem -Path $py | Out-Null  # test path exists
        $Python = & py "-$pyver" -c "import sys;print(sys.executable)"
        #$pipenv = & py "-$pyver" -c "import sys;import os;print(os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pipenv'));"
    }

    # update the shell window title with information about the virtual environment
    $py_ver = & $Python --version
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
