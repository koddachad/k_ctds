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

# _tds.pyd is installed inside k_ctds/ in site-packages.
# On Python 3.8+, Windows no longer searches PATH for DLL dependencies of extension
# modules, so the DLLs must be placed alongside _tds.pyd or registered via os.add_dll_directory().
$site_packages = "$env:PYTHON\Lib\site-packages"
Write-Output "Copying DLLs to site-packages root: $site_packages"
Copy-Item "$env:BUILD_INSTALL_PREFIX\lib\*.dll" "$site_packages\"

# Also verify _tds.pyd is where we expect it.
$tds_pyd = Get-ChildItem "$site_packages\_tds*.pyd" -ErrorAction SilentlyContinue
if ($tds_pyd) {
    Write-Output "Found _tds extension: $($tds_pyd.FullName)"
} else {
    Write-Warning "_tds.pyd not found in $site_packages - DLL loading may fail"
}

if ($LastExitCode -ne 0) { exit $LastExitCode }
