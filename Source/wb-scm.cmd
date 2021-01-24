@echo off
setlocal
if "%BUILDER_TOP_DIR%" == "" (
    echo Info: Bootstrap the build environment
    set BUILDER_START_DIR=%CD%
    :scan
        if exist Builder goto found
        for %%I in (%CD%) do set __builder_tmp=%%~pI
        if "%__builder_tmp%" == "\" goto not_found
        cd ..
        goto scan

    :not_found
        echo Error: Cannot find the Builder folder
        goto :eof

    :found
        set __builder_tmp=
        set BUILDER_TOP_DIR=%CD%

        cd Builder
        echo Info: Builder running builder_custom_init.cmd
        call builder_custom_init.cmd
        cd %BUILDER_START_DIR%
)

if "%PYTHON%" == "" (
    echo Error: PYTHON is not set
    echo Make sure Builder\builder_custom_init.cmd has been run
    goto :eof
)

set PYTHONPATH=%BUILDER_TOP_DIR%\Source\Scm;%BUILDER_TOP_DIR%\Source\Common;%BUILDER_TOP_DIR%\Source\Git;%BUILDER_TOP_DIR%\Source\Svn;%BUILDER_TOP_DIR%\Source\Hg

call %BUILDER_TOP_DIR%\Kit\Windows\build-extras.cmd testing

set PROG=scm_workbench_git_callback.cmd
echo "%PYTHON%" "%BUILDER_TOP_DIR%\Source\Git\wb_git_callback_client_win32.py" %%1 %%2 >%PROG%

set BUILDER_START_DIR=
set BUILDER_TOP_DIR=
set BUILDROOT_DIR=

echo PYTHONPATH %PYTHONPATH%
%PYTHON% wb_scm_main.py %*
if errorlevel 1 echo Error: wb_scm_main exited with error
endlocal
