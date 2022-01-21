#!powershell
#
# uninstall, build, install coverlovin2
# this is mostly used to test changes in `setup.py`

$PYTHON = "python.exe"
if ($env:PYTHON -ne $null) {
    $PYTHON = $env:PYTHON
}

$ErrorActionPreference = "Stop"
$DebugPreference = "Continue"
Push-Location "$PSScriptRoot/../.."
Set-PSDebug -Trace 1

function Print-Files-Coverlovin2
{
    Set-PSDebug -Trace 0
    if (-Not (Test-Path "${env:VIRTUAL_ENV}"))
    {
        Set-PSDebug -Trace 1
        return
    }
    & {
        Get-ChildItem -Path "${env:VIRTUAL_ENV}" -Filter "coverlovin2*" -File -Recurse
        Get-ChildItem -Path "${env:VIRTUAL_ENV}" -Filter "app.py*" -File -Recurse
        Get-ChildItem -Path "${env:VIRTUAL_ENV}" -Filter "coverlovin2*" -Recurse -Dir | Get-ChildItem -Recurse
    } | Select-Object -Unique | Sort-Object `
      | Format-Table -Property FullName, Length, CreationTime

      #| Where-Object  {$_.Name -ne "__pycache__"} `
      #| Where-Object  {$_.Name -notcontains ".pyc"} `

    Set-PSDebug -Trace 1
}

function Print-Files-In-Archive
{
    Param([Parameter(mandatory = $true)] [System.IO.FileInfo] $fpath)

    Set-PSDebug -Trace 0
    if (-Not (Test-Path $fpath))
    {
        Write-Error "Path does not exist '${fpath}'"
        return
    }
    Write-Host "Files in archive '$fpath'"
    # copied from https://stackoverflow.com/a/14204577/471376
    [Reflection.Assembly]::LoadWithPartialName("System.IO.Compression.FileSystem")
    [IO.Compression.ZipFile]::OpenRead($fpath.FullName).Entries.FullName | `
            %{ "$fpath`:$_" }

    Set-PSDebug -Trace 1
}

try {
    # uninstall prior
    & $PYTHON -m pip uninstall -v --disable-pip-version-check --yes coverlovin2
    Set-PSDebug -Trace 0
    # thoroughly delete everything from prior install
    foreach (
        $fd in
        @(
            "${env:VIRTUAL_ENV}\Lib\site-packages\coverlovin2\test"
            "${env:VIRTUAL_ENV}\Lib\site-packages\coverlovin2\__pycache__"
            "${env:VIRTUAL_ENV}\Lib\site-packages\__pycache__\coverlovin2.cpython-39.pyc"
            "${env:VIRTUAL_ENV}\Scripts\coverlovin2.py"
            "${env:VIRTUAL_ENV}\Scripts\coverlovin2.exe"
            "${env:VIRTUAL_ENV}\Scripts\app.py"
            "${env:VIRTUAL_ENV}\Scripts\__pycache__\coverlovin2.cpython-39.pyc"
        )
    )
    {
        if (Test-Path $fd)
        {
            Remove-Item -Verbose -Recurse $fd
        }
    }
    Print-Files-Coverlovin2
    Set-PSDebug -Trace 1

    # install latest
    Push-Location "$PSScriptRoot/.."
    & $PYTHON "./setup.py" bdist_wheel
    $distf = Get-ChildItem -File -LiteralPath "./dist/" | Sort-Object | Select-Object -Last 1
    Print-Files-In-Archive $distf
    Pop-Location
    & $PYTHON -m pip install `
        --verbose --debug --disable-pip-version-check --force-reinstall `
        $distf
    Print-Files-Coverlovin2
} finally {
    # XXX: presuming these were the prior settings
    Pop-Location
    Set-PSDebug -Trace 0
    $DebugPreference = "SilentlyContinue"
}
