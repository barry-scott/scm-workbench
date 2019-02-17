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

call %BUILDER_TOP_DIR%\Kit\Windows\build-check-pip-deps.cmd testing

set PYTHONPATH=%BUILDER_TOP_DIR%\Source\Scm;%BUILDER_TOP_DIR%\Source\Common;%BUILDER_TOP_DIR%\Source\Git;%BUILDER_TOP_DIR%\Source\Svn;%BUILDER_TOP_DIR%\Source\Hg

cd ..\Common
    %PYTHON% make_wb_diff_images.py
    if errorlevel 1 goto :eof

cd ..\Scm
echo Info: Build Clean
    if exist locale rmdir /s /q locale
    echo zzz >I18N\zzzqqqzzz.current.po
    del I18N\*.current.po
    if exist wb_scm_images.py del wb_scm_images.py
    if exist wb_scm_version.py del wb_scm_version.py

echo Info: Build all
    %PYTHON% -u make_wb_scm_images.py
    %PYTHON% -u make_wb_scm_version.py %BUILDER_TOP_DIR%/Builder/version.dat wb_scm_version.py
    if not exist locale\en\LC_MESSAGES mkdir locale\en\LC_MESSAGES
    for /F "usebackq" %%X in ('xgettext.exe') do set XGETTXT_PATH=MISSING%%~$PATH:X
    if "%XGETTXT_PATH%" == "MISSING" (
        echo Warning: cannot make translation MO files - cannot find xgettext.exe
    ) else (
        cd I18N
        %PYTHON% make_pot_file.py
        %PYTHON% make_po_file.py en
        %PYTHON% make_mo_files.py ..\locale
        cd ..
    )
set PROG=scm_workbench_git_callback.cmd
echo "%PYTHON%" "%BUILDER_TOP_DIR%\Source\Git\wb_git_callback_client_win32.py" %%1 %%2 >%PROG%

set BUILDER_START_DIR=
set BUILDER_TOP_DIR=
set BUILDROOT_DIR=

echo PYTHONPATH %PYTHONPATH%
%PYTHON% wb_scm_main.py %*
if errorlevel 1 echo Error: wb_scm_main exited with error
endlocal
