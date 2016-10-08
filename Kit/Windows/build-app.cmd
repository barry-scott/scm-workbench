@echo off
setlocal

rem
rem     build-app.cmd
rem
echo Info: build-app.cmd
if "%BUILDER_TOP_DIR%" == "" (
    echo BUILDER_TOP_DIR is not defined - hint builder not run?
    exit /b 1
)
if "%1" == "--debug" (
    shift
    set VERBOSE=--verbose
    echo on
)

set APPMODE=--gui
if "%1" == "--cli" set APPMODE=--cli

set PKG_DIST_DIR=%BUILDER_TOP_DIR%\Kit\Windows\app.tmp
set SRC_DIR=%BUILDER_TOP_DIR%\Source

set DIST_DIR=%PKG_DIST_DIR%

if exist build rmdir /s /q build
    if errorlevel 1 goto :error
if exist %DIST_DIR% rmdir /s /q %DIST_DIR%
    if errorlevel 1 goto :error
if exist setup.tmp rmdir /s /q setup.tmp
    if errorlevel 1 goto :error

mkdir %DIST_DIR%
    if errorlevel 1 goto :error

pushd %SRC_DIR%\Common
%PYTHON% make_wb_diff_images.py
    if errorlevel 1 goto :error
popd >NUL

pushd %SRC_DIR%\Scm
nmake -f windows.mak clean
nmake -f windows.mak
    if errorlevel 1 goto :error
popd >NUL

set PYTHONPATH=%SRC_DIR%\Scm;%SRC_DIR%\Git;%SRC_DIR%\Svn;%SRC_DIR%\Hg;%SRC_DIR%\Common
pushd %SRC_DIR%\Scm
%PYTHON% -m win_app_packager build wb_scm_main.py %APPMODE% %DIST_DIR% --icon %SRC_DIR%\wb.ico --name "SCM Workbench" --modules-allowed-to-be-missing-file %BUILDER_TOP_DIR%\Kit\Windows\modules-allowed-to-be-missing.txt %VERBOSE%
    if errorlevel 1 goto :error
popd >NUL
pushd %SRC_DIR%\Git
%PYTHON% -m win_app_packager build wb_git_askpass_client_win32.py --cli %DIST_DIR% --icon %SRC_DIR%\wb.ico --name "SCM-Workbench-AskPass" --merge %VERBOSE%
    if errorlevel 1 goto :error
popd >NUL

goto :eof
echo Info: Remove unneeded files
del %DIST_DIR%\PyWinAppRes\Lib\distutils\command\wininst-*.exe
del %DIST_DIR%\PyWinAppRes\Lib\site-packages\pysvn\unins000.*
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\site-packages\PyQt5\Qt\qsci\api
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\ctypes\test
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\site-packages\git\test
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\site-packages\gitdb\test
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\site-packages\smmap\test
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\unittest\test

echo Info: build-app.cmd done
goto :eof
:error
    echo Error: Build failed.
    exit /b 1

endlocal
