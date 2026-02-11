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

# Download and run Codecov uploader
Invoke-WebRequest -Uri "https://uploader.codecov.io/latest/windows/codecov.exe" -OutFile codecov.exe
& .\codecov.exe -f "coverage.xml" -f "cobertura.xml" -t "$env:CODECOV_TOKEN"
if ($LastExitCode -ne 0) { exit $LastExitCode }
