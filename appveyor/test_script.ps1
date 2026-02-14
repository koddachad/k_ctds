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

& "$env:PYTHON\Scripts\check-manifest" -v
if ($LastExitCode -ne 0) { exit $LastExitCode }

# Add FreeTDS library dir to PATH so shared libs will be found.
# NOTE: On Python 3.8+, PATH is no longer searched for DLL dependencies of
# extension modules. The DLLs should be in site-packages alongside _tds.pyd
# (handled by build_script.ps1), but we also add the directory via
# os.add_dll_directory() as a fallback.
$env:PATH += ";$env:BUILD_INSTALL_PREFIX\lib"

Write-Output "Contents of $env:BUILD_INSTALL_PREFIX\lib:"
Get-ChildItem "$env:BUILD_INSTALL_PREFIX\lib" | Format-Table Name, Length
Write-Output "FreeTDS build directory:"
Get-ChildItem "$env:APPVEYOR_BUILD_FOLDER\build\freetds-$env:FREETDS_VERSION\src\dblib" -ErrorAction SilentlyContinue | Format-Table Name, Length
Get-ChildItem "$env:APPVEYOR_BUILD_FOLDER\build\freetds-$env:FREETDS_VERSION\src\tds" -ErrorAction SilentlyContinue | Format-Table Name, Length

# The computer's hostname is returned in messages from SQL Server.
$env:HOSTNAME = "$env:COMPUTERNAME"

& "$env:PYTHON\python.exe" -c @"
import os, sys
dll_dir = os.path.join(r'$env:BUILD_INSTALL_PREFIX', 'lib')
print(f'Adding DLL directory: {dll_dir}')
print(f'DLL dir exists: {os.path.isdir(dll_dir)}')
print(f'DLL dir contents: {os.listdir(dll_dir)}')
if hasattr(os, 'add_dll_directory'):
    os.add_dll_directory(dll_dir)
    print('os.add_dll_directory() called successfully')
import k_ctds
print(f'k_ctds imported successfully, freetds_version={k_ctds.freetds_version}')
"@


& "$env:ProgramFiles\OpenCppCoverage\OpenCppCoverage.exe" `
    --export_type=cobertura:cobertura.xml --optimized_build `
    --sources "$env:APPVEYOR_BUILD_FOLDER\src" `
    --modules "$env:APPVEYOR_BUILD_FOLDER" -- `
    "$env:PYTHON\python.exe" -m coverage run --branch --source 'k_ctds' -m pytest -vv tests/
if ($LastExitCode -ne 0) { exit $LastExitCode }

& "$env:PYTHON\Scripts\coverage" report -m --skip-covered
if ($LastExitCode -ne 0) { exit $LastExitCode }

& "$env:PYTHON\Scripts\coverage" xml
if ($LastExitCode -ne 0) { exit $LastExitCode }
