@echo off
setlocal

rem
rem     build-app.cmd
rem
colour-print "<>info Info:<> build-app.cmd"
if "%BUILDER_TOP_DIR%" == "" (
    echo BUILDER_TOP_DIR is not defined - hint builder not run?
    exit /b 1
)
if "%1" == "--debug" (
    shift
    set VERBOSE=--verbose
    echo on
)

rem add location of python used to create the venv to the path
rem so that python DLLs can be found
for %%i in (%PYTHON%) do set PATH=%%~di%%~pi;%PATH%

set PYTHON=%BUILDER_TOP_DIR%\Kit\Windows\venv.tmp\scripts\python.exe

set APPMODE=--gui
if "%1" == "--cli" set APPMODE=--cli

set DIST_DIR=%BUILDER_TOP_DIR%\Kit\Windows\app.tmp
set SRC_DIR=%BUILDER_TOP_DIR%\Source
set DOC_DIR=%BUILDER_TOP_DIR%\Docs

if exist build rmdir /s /q build
    if exist build goto :error
if exist %DIST_DIR% rmdir /s /q %DIST_DIR%
    if exist %DIST_DIR% goto :error
if exist setup.tmp rmdir /s /q setup.tmp
    if exist setup.tmp goto :error

mkdir %DIST_DIR%
    if errorlevel 1 goto :error
rem set the version
call %SRC_DIR%\Scm\wb_scm_version.cmd

set PYTHONPATH=%SRC_DIR%\Scm;%SRC_DIR%\Git;%SRC_DIR%\Svn;%SRC_DIR%\Hg;%SRC_DIR%\Perforce;%SRC_DIR%\Common
pushd %SRC_DIR%\Scm
colour-print "<>info Info:<> Build SCM Workbench %APPMODE%"
%PYTHON% -m win_app_packager build wb_scm_main.py %APPMODE% %DIST_DIR% --version %WB_SCM_VERSION% --icon %SRC_DIR%\wb.ico --name "SCM Workbench" --modules-allowed-to-be-missing-file %BUILDER_TOP_DIR%\Kit\Windows\modules-allowed-to-be-missing.txt %VERBOSE%
    if errorlevel 1 goto :error
popd >NUL
pushd %SRC_DIR%\Git
colour-print "<>info Info:<> Build git callback client"
%PYTHON% -m win_app_packager build wb_git_callback_client_win32.py --cli %DIST_DIR% --version %WB_SCM_VERSION% --icon %SRC_DIR%\wb.ico --name "SCM-Workbench-Git-Callback" --merge %VERBOSE%
    if errorlevel 1 goto :error
popd >NUL

colour-print "<>info Info:<> Copy in the docs"
%DOC_DIR%\build-docs.py %DIST_DIR%\Documentation
    if errorlevel 1 goto :error

pushd %DIST_DIR%\PyWinAppRes\Lib\site-packages\PyQt5
    if errorlevel 1 goto :error

colour-print "<>info Info:<> clean up Qt 1. move all pyd and dll into a tmp folder"
mkdir tmp
    if errorlevel 1 goto :error
move Qt*.pyd tmp >NUL
    if errorlevel 1 goto :error
move tmp\Qt.pyd . >NUL
    if errorlevel 1 goto :error

mkdir Qt\bin\tmp
    if errorlevel 1 goto :error
move Qt\bin\Qt5*.dll Qt\bin\tmp >NUL
    if errorlevel 1 goto :error

colour-print "<>info Info:<> clean up Qt 2. bring back only the ones we use"
for %%x in (Core DBus Gui PrintSupport Svg Widgets) do call :qt_keep %%x

colour-print "<>info Info:<> clean up Qt 3. delete the Qt files we do not need"
rmdir /s /q tmp
    if errorlevel 1 goto :error
rmdir /s /q Qt\bin\tmp
    if errorlevel 1 goto :error

colour-print "<>info Info:<> clean up Qt 4. delete qml file"
rmdir /s /q Qt\qml
    if errorlevel 1 goto :error

colour-print "<>info Info:<> clean up Qt 5. delete translations file"
rmdir /s /q Qt\translations
    if errorlevel 1 goto :error

colour-print "<>info Info:<> clean up Qt 6. delete webengine files"
if exist Qt\bin\QtWebEngineProcess.exe (
    del Qt\bin\QtWebEngineProcess.exe >NUL
        if errorlevel 1 goto :error
    del Qt\resources\qtwebengine*.pak >NUL
        if errorlevel 1 goto :error
)

colour-print "<>info Info:<> clean up Qt 6. delete qsci resources"
rmdir /s /q Qt\qsci
    if errorlevel 1 goto :error


colour-print "<>info Info:<> clean up python lib 1. delete test code"
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\ctypes\test
    if errorlevel 1 goto :error
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\site-packages\git\test
    if errorlevel 1 goto :error
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\site-packages\gitdb\test
    if errorlevel 1 goto :error
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\site-packages\smmap\test
    if errorlevel 1 goto :error
rmdir /s /q %DIST_DIR%\PyWinAppRes\Lib\unittest\test
    if errorlevel 1 goto :error

colour-print "<>info Info:<> clean up python lib 2. delete distutils exe"
del /s %DIST_DIR%\PyWinAppRes\Lib\distutils\command\wininst-*.exe >NUL
    if errorlevel 1 goto :error

colour-print "<>info Info:<> clean up python lib 3. delete pysvn uninstall exe"
del /s %DIST_DIR%\PyWinAppRes\Lib\site-packages\pysvn\unins000.exe >NUL
    if errorlevel 1 goto :error

popd

colour-print "<>info Info:<> build-app completed successfully"
exit /b 0
endlocal

:qt_keep
    colour-print "<>info Info:<> Keeping Qt%1"
    move tmp\Qt%1.pyd . >NUL
        if errorlevel 1 goto :error
    move Qt\bin\tmp\Qt5%1.dll Qt\bin >NUL
        if errorlevel 1 goto :error
    goto :eof

:error
    echo Error: build-app failed
    exit /b 1

