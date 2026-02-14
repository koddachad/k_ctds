@ECHO OFF

SET COMMAND_TO_RUN=%*

REM Assume that VCINSTALL implies running this script is running in an
REM MSVC-configured environment.

IF NOT DEFINED VCINSTALL (
    FOR %%x IN (
    "%PROGRAMFILES%\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat"
    "%PROGRAMFILES%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
    "%PROGRAMFILES%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
    "%PROGRAMFILES%\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat"
    
     ) DO (
        IF EXIST %%x (
            SET VCVARS=%%x
            GOTO :setup_env
        )
    )
    ECHO Failed to detect MSVC tool chain.
    EXIT 1

:setup_env
    CALL %VCVARS% amd64
)

CALL %COMMAND_TO_RUN% || EXIT 1
