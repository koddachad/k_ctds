$ErrorActionPreference = "Stop"

# Explicitly enable modern versions of TLS.
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Function MSVC-Env-Invoke([string] $command)
{
    $command = "$env:COMSPEC /E:ON /V:ON /C $PSScriptRoot\run_with_msvc.cmd " + $command
    $output = Invoke-Expression -Command:$command
    Write-Output $output
    if ($LastExitCode -ne 0) { exit $LastExitCode }
}

Function Ensure-Dir([string] $Path)
{
    if (-not (Test-Path -Path $Path))
    {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

Function Cached-Download([string] $Url, [string] $OutputFile, [string[]] $FallbackUrls = @())
{
    if (-not (Test-Path -Path $OutputFile))
    {
        $allUrls = @($Url) + $FallbackUrls
        foreach ($downloadUrl in $allUrls)
        {
            for ($attempt = 1; $attempt -le 10; $attempt++)
            {
                try
                {
                    Write-Verbose "Downloading $OutputFile from '$downloadUrl' (attempt $attempt) ..."
                    (New-Object System.Net.WebClient).DownloadFile($downloadUrl, $OutputFile)
                    return
                }
                catch
                {
                    Write-Warning "Download attempt $attempt from '$downloadUrl' failed: $_"
                    if ($attempt -lt 3) { Start-Sleep -Seconds 5 }
                }
            }
        }
        throw "Failed to download $OutputFile from all sources."
    }
}


set-alias extract "$env:ProgramFiles\7-Zip\7z.exe"

#
# Build win-iconv.
#
if (Test-Path env:WIN_ICONV_VERSION)
{
    $win_iconv_version = $env:WIN_ICONV_VERSION
}
else
{
    $win_iconv_version = "0.0.10"
    Write-Verbose "WIN_ICONV_VERSION not set; defaulting to $win_iconv_version"
}

$build_dir = "$PSScriptRoot\..\build"

if (Test-Path env:BUILD_INSTALL_PREFIX)
{
    $install_prefix = $env:BUILD_INSTALL_PREFIX
}
else
{
    $install_prefix = $build_dir
}

Ensure-Dir $build_dir
Ensure-Dir "$install_prefix\include"
Ensure-Dir "$install_prefix\lib"


$url = "https://github.com/win-iconv/win-iconv/archive/v$win_iconv_version.zip"
$win_iconv_zip = "$build_dir\win-iconv-$win_iconv_version.zip"

Cached-Download $url $win_iconv_zip

$win_iconv_path = "win-iconv-$win_iconv_version"

if (-not (Test-Path -Path $win_iconv_path))
{
    # Requires PowerShell 5+.
    Write-Verbose "Expanding $win_iconv_zip ..."
    extract x -aoa "$win_iconv_zip" -o"$build_dir"
    if ($LastExitCode -ne 0) { exit $LastExitCode }
}

pushd "$build_dir\$win_iconv_path"

$cmake = "``
cmake -G ""NMake Makefiles"" ``
    -DBUILD_STATIC=on ``
    -DBUILD_SHARED=off ``
    -DBUILD_EXECUTABLE=off ``
    -DCMAKE_BUILD_TYPE=Release ``
    .
"

MSVC-Env-Invoke $cmake
MSVC-Env-Invoke 'nmake'

popd

# Copy lib and include files to common dir.
cp "$build_dir\$win_iconv_path\iconv.h" "$install_prefix\include"
cp "$build_dir\$win_iconv_path\*.lib" "$install_prefix\lib"

#
# Build FreeTDS
#
if (Test-Path env:FREETDS_VERSION)
{
    $freetds_version = $env:FREETDS_VERSION
}
else
{
    $freetds_version = "1.5.21"
    Write-Verbose "FREETDS_VERSION not set; defaulting to $freetds_version"
}

$freetds_tar = "$build_dir\freetds-$freetds_version.tar"
$freetds_path = "$build_dir\freetds-$freetds_version"

$url = "https://www.freetds.org/files/stable/freetds-$freetds_version.tar.gz"

Cached-Download $url "$freetds_path.tar.gz"


if (-not (Test-Path -Path $freetds_path))
{
    Write-Verbose "Expanding $freetds_path.tar.gz ..."
    extract x -aoa "$freetds_path.tar.gz" -o"$build_dir"
    extract x -aoa "$freetds_path.tar" -o"$build_dir"
    if ($LastExitCode -ne 0) { exit $LastExitCode }
}

pushd "$freetds_path"

# Apply the k_ctds FreeTDS patch (Microsoft Entra ID token authentication), if
# one exists for this version. The build fails if the patch neither applies
# nor is already applied, so a wheel can never silently ship without it.
$freetds_patch = Join-Path (Split-Path -Parent $PSScriptRoot) "freetds\fedauth-$freetds_version.patch"
if (Test-Path -Path $freetds_patch)
{
    git apply --check --ignore-whitespace "$freetds_patch" 2>$null
    if ($LastExitCode -eq 0)
    {
        Write-Host "Applying $freetds_patch ..."
        git apply --ignore-whitespace "$freetds_patch"
        if ($LastExitCode -ne 0) { exit $LastExitCode }
    }
    else
    {
        git apply --check --reverse --ignore-whitespace "$freetds_patch" 2>$null
        if ($LastExitCode -eq 0)
        {
            Write-Host "$freetds_patch is already applied; skipping."
        }
        else
        {
            Write-Error "$freetds_patch does not apply to FreeTDS $freetds_version"
            exit 1
        }
    }
}

#
# TLS: build FreeTDS against OpenSSL so the wheel can talk to servers that
# require encryption (Azure SQL always does). The GitHub Windows runner image
# ships OpenSSL 3 under "C:\Program Files\OpenSSL"; override with
# OPENSSL_ROOT_DIR for other machines. Building without TLS is an error, not a
# fallback, so a wheel can never silently lose encryption support.
#
if (Test-Path env:OPENSSL_ROOT_DIR)
{
    $openssl_root = $env:OPENSSL_ROOT_DIR
}
else
{
    $openssl_root = "$env:ProgramFiles\OpenSSL"
    Write-Verbose "OPENSSL_ROOT_DIR not set; defaulting to $openssl_root"
}
if (-not (Test-Path -Path "$openssl_root\include\openssl\ssl.h"))
{
    Write-Error "OpenSSL not found at $openssl_root (set OPENSSL_ROOT_DIR)"
    exit 1
}

$cmake = "``
cmake -G ""NMake Makefiles"" ``
    -DCMAKE_BUILD_TYPE=Release ``
    -DCMAKE_INSTALL_PREFIX=""$build_dir"" ``
    -DWITH_OPENSSL=ON ``
    -DOPENSSL_ROOT_DIR=""$openssl_root"" ``
    -DWITH_GNUTLS=OFF ``
    -DCMAKE_PREFIX_PATH=""$install_prefix"" ``
    .
"

MSVC-Env-Invoke $cmake

# cmake only reports OpenSSL as a status line; make sure it was really found.
$cmake_cache = Get-Content "$freetds_path\CMakeCache.txt" -Raw
if ($cmake_cache -notmatch "OPENSSL_INCLUDE_DIR:PATH=(?!OPENSSL_INCLUDE_DIR-NOTFOUND)")
{
    Write-Error "cmake did not find OpenSSL under $openssl_root"
    exit 1
}

MSVC-Env-Invoke 'nmake all'

# Stage the OpenSSL runtime DLLs next to the FreeTDS DLLs. delvewheel picks
# them up from build\lib (see pyproject.toml) and bundles them into the wheel.
# Only OpenSSL 3 DLLs (libssl-3-x64.dll, libcrypto-3-x64.dll) are accepted:
# THIRD_PARTY_NOTICES documents the Apache-2.0 licensed OpenSSL 3, and 1.1.1
# is end-of-life.
$openssl_dlls = Get-ChildItem -Path "$openssl_root\bin" -Filter "lib*-3*.dll" -ErrorAction SilentlyContinue
if (-not $openssl_dlls)
{
    Write-Error "no OpenSSL 3 DLLs (lib*-3*.dll) found under $openssl_root\bin"
    exit 1
}
foreach ($dll in $openssl_dlls)
{
    Write-Host "Staging $($dll.FullName)"
    cp $dll.FullName "$install_prefix\lib"
}

# $TODO: Is there no "install" target in freetds for nmake?!?
cp "$freetds_path\include\*.h" "$install_prefix\include"
cp "$freetds_path\src\dblib\*.lib" "$install_prefix\lib"
cp "$freetds_path\src\dblib\*.dll" "$install_prefix\lib"
cp "$freetds_path\src\ctlib\*.lib" "$install_prefix\lib"
cp "$freetds_path\src\ctlib\*.dll" "$install_prefix\lib"
cp "$freetds_path\src\tds\*.lib" "$install_prefix\lib"
cp "$freetds_path\src\tds\*.dll" "$install_prefix``\lib" -ErrorAction SilentlyContinue

popd
