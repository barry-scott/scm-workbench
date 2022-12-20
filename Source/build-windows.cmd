@echo off
setlocal

rem
rem     build-windows.cmd
rem
if "%BUILDER_TOP_DIR%" == "" (
    echo BUILDER_TOP_DIR is not defined - hint builder not run?
    exit /b 1
)

set VENV_BIN=%BUILDER_TOP_DIR%\Builder\venv.tmp\scripts
set PYTHON=%VENV_BIN%\python.exe

%VENV_BIN%\colour-print "<>info Info:<> build-windows.cmd"
if "%1" == "--debug" (
    shift
    set VERBOSE=--verbose
    echo on
)

rem add location of python used to create the venv to the path
rem so that python DLLs can be found
for %%i in (%PYTHON%) do set PATH=%%~di%%~pi;%PATH%

set APPMODE=--gui
if "%1" == "--gui" (
    set APPMODE=--gui
    shift
)
if "%1" == "--cli" (
    set APPMODE=--cli
    shift
)

if not exist "%1" (
    %VENV_BIN%\colour-print "<>error Error:<> build-windows.cmd DIST_DIR %1 does not exist"
    exit /b 1
)

if "%2" == "" (
    %VENV_BIN%\colour-print "<>error Error:<> build-windows.cmd version %2 missing"
    exit /b  1
)
set WB_VERSION=%2

set DIST_DIR=%1
set SRC_DIR=%BUILDER_TOP_DIR%\Source

if exist build rmdir /s /q build
    if exist build goto :error
if exist %DIST_DIR% rmdir /s /q %DIST_DIR%
    if exist %DIST_DIR% goto :error
if exist setup.tmp rmdir /s /q setup.tmp
    if exist setup.tmp goto :error

mkdir %DIST_DIR%
    if errorlevel 1 goto :error
rem set the version

%VENV_BIN%\colour-print "<>info Info:<> Generate SCM resource sources"
set TMP_SRC=%BUILDER_TOP_DIR%\Builder\tmp\Source
if exist %TMP_SRC% rmdir /s /q %TMP_SRC%
mkdir %TMP_SRC%

"%PYTHON%" %SRC_DIR%\make_wb_scm_version.py ^
    %BUILDER_TOP_DIR%\Builder\version.dat ^
    %TMP_SRC%\wb_scm_version.py

"%PYTHON%" %SRC_DIR%\make_wb_scm_images.py ^
    %TMP_SRC%\wb_scm_images.py
dir %TMP_SRC%

%VENV_BIN%\colour-print "<>info Info:<> Build SCM Workbench %APPMODE% version %WB_VERSION%"
set PYTHONPATH=%TMP_SRC%;%SRC_DIR%\Scm;%SRC_DIR%\Git;%SRC_DIR%\Svn;%SRC_DIR%\Hg;%SRC_DIR%\Perforce;%SRC_DIR%\Common
pushd %SRC_DIR%\Scm
"%PYTHON%" -m win_app_packager build wb_scm_main.py ^
        %APPMODE% %DIST_DIR% ^
        --version %WB_VERSION% ^
        --icon %SRC_DIR%\wb.ico ^
        --name "SCM Workbench" ^
        --modules-allowed-to-be-missing-file %BUILDER_TOP_DIR%\Builder\win-modules-allowed-to-be-missing.txt ^
        %VERBOSE%
    if errorlevel 1 goto :error
popd >NUL

%VENV_BIN%\colour-print "<>info Info:<> Build git callback client"
pushd %SRC_DIR%\Git
"%PYTHON%" -m win_app_packager build wb_git_callback_client_win32.py ^
        --cli %DIST_DIR% ^
        --version %WB_VERSION% ^
        --icon %SRC_DIR%\wb.ico ^
        --name "SCM-Workbench-Git-Callback" ^
        --merge ^
        %VERBOSE%
    if errorlevel 1 goto :error
popd >NUL

%VENV_BIN%\colour-print "<>info Info:<> Copy in the docs"
"%PYTHON%" %BUILDER_TOP_DIR%\Docs\build-docs.py %DIST_DIR%\Documentation
    if errorlevel 1 goto :error

echo on
%VENV_BIN%\colour-print "<>info Info:<> clean up Qt 1. move all pyd and dll into a tmp folder"
pushd %DIST_DIR%\PyWinAppRes\Lib\site-packages\PyQt5
    if errorlevel 1 goto :error

mkdir tmp
    if errorlevel 1 goto :error
move Qt*.pyd tmp >NUL
    if errorlevel 1 goto :error
move tmp\Qt.pyd . >NUL
    if errorlevel 1 goto :error

mkdir Qt5\bin\tmp
    if errorlevel 1 goto :error
move Qt5\bin\Qt5*.dll Qt5\bin\tmp >NUL
    if errorlevel 1 goto :error

%VENV_BIN%\colour-print "<>info Info:<> clean up Qt 2. bring back only the ones we use"
for %%x in (Core DBus Gui PrintSupport Svg Widgets) do call :qt_keep %%x

%VENV_BIN%\colour-print "<>info Info:<> clean up Qt 3. delete the Qt files we do not need"
rmdir /s /q tmp
    if errorlevel 1 goto :error
rmdir /s /q Qt5\bin\tmp
    if errorlevel 1 goto :error

%VENV_BIN%\colour-print "<>info Info:<> clean up Qt 4. delete qml file"
rmdir /s /q Qt5\qml
    if errorlevel 1 goto :error

%VENV_BIN%\colour-print "<>info Info:<> clean up Qt 5. delete translations file"
rmdir /s /q Qt5\translations
    if errorlevel 1 goto :error

%VENV_BIN%\colour-print "<>info Info:<> clean up Qt 6. delete webengine files"
if exist Qt5\bin\QtWebEngineProcess.exe (
    del Qt5\bin\QtWebEngineProcess.exe >NUL
        if errorlevel 1 goto :error
    del Qt5\resources\qtwebengine*.pak >NUL
        if errorlevel 1 goto :error
)

%VENV_BIN%\colour-print "<>info Info:<> clean up Qt 6. delete qsci resources"
rmdir /s /q Qt5\qsci
    if errorlevel 1 goto :error

%VENV_BIN%\colour-print "<>info Info:<> clean up python lib 1. delete test code"
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\ctypes\test
    if errorlevel 1 goto :error
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\site-packages\gitdb\test
    if errorlevel 1 goto :error
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\site-packages\smmap\test
    if errorlevel 1 goto :error
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\unittest\test
    if errorlevel 1 goto :error
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\test
    if errorlevel 1 goto :error
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\tkinter
    if errorlevel 1 goto :error

%VENV_BIN%\colour-print "<>info Info:<> clean up python lib 2. delete distutils exe"
del /s %DIST_DIR%\PyWinAppRes\Lib\distutils\command\wininst-*.exe >NUL
    if errorlevel 1 goto :error

%VENV_BIN%\colour-print "<>info Info:<> clean up python lib 3. delete pysvn uninstall exe"
del /s %DIST_DIR%\PyWinAppRes\Lib\site-packages\pysvn\unins000.exe >NUL
    if errorlevel 1 goto :error

popd

%VENV_BIN%\colour-print "<>info Info:<> build-app completed successfully"
exit /b 0
endlocal

:qt_keep
    %VENV_BIN%\colour-print "<>info Info:<> Keeping Qt%1"
    move tmp\Qt%1.pyd . >NUL
        if errorlevel 1 goto :error
    move Qt\bin\tmp\Qt5%1.dll Qt\bin >NUL
        if errorlevel 1 goto :error
    goto :eof

:error
    echo Error: build-app failed
    exit /b 1
