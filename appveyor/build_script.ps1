$ErrorActionPreference = "Stop"

if ($env:APPVEYOR -ne "True")
{
    Write-Output "$PSCommandPath should only be run in the Appveyor-ci environment."
    exit 1
}

if (-not (Test-Path env:PYTHON))
{
    Write-Output "PYTHON environment variable not set."
    exit 1
}

# Set include and lib paths.
$env:CTDS_INCLUDE_DIRS = "$env:BUILD_INSTALL_PREFIX\include"
$env:CTDS_LIBRARY_DIRS= "$env:BUILD_INSTALL_PREFIX\lib"

$env:CTDS_STRICT = 1
$env:CTDS_COVER = 1

& "$env:PYTHON\python.exe" -m pip install .

$site_packages = (& "$env:PYTHON\python.exe" -c "import site; print(site.getsitepackages()[0])").Trim()
Write-Output "Copying DLLs to: $site_packages\ctds\"
Copy-Item "$env:BUILD_INSTALL_PREFIX\lib\*.dll" "$site_packages\ctds\"


if ($LastExitCode -ne 0) { exit $LastExitCode }
