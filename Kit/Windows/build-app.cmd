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
if "%BUILDER_QTDIR%" == "" (
    echo BUILDER_QTDIR is not defined - hint  update builder_custom_init.cmd?
    exit /b 1
)
if not exist "%BUILDER_QTDIR%" (
    echo BUILDER_QTDIR folder does not exist - hint update builder_custom_init.cmd?
    exit /b 1
)

set PKG_DIST_DIR=%BUILDER_TOP_DIR%\Kit\Windows\pkg
set SRC_DIR=%BUILDER_TOP_DIR%\Source
set KIT_DIR=%BUILDER_TOP_DIR%\Kit\macOS

set DIST_DIR=%PKG_DIST_DIR%

if exist build rmdir /s /q build
    if errorlevel 1 goto :eof
if exist %DIST_DIR% rmdir /s /q %DIST_DIR%
    if errorlevel 1 goto :eof
if exist tmp rmdir /s /q tmp
    if errorlevel 1 goto :eof

mkdir %DIST_DIR%
    if errorlevel 1 goto :eof

pushd %SRC_DIR%\Common
%PYTHON% make_wb_diff_images.py
    if errorlevel 1 goto :eof
popd >null

pushd %SRC_DIR%\Scm
nmake -f windows.mak
    if errorlevel 1 goto :eof
popd >null

set PATH=%BUILDER_QTDIR%\msvc2015_64\bin;%PATH%
set PYTHONPATH=%SRC_DIR%\Scm;%SRC_DIR%\Git;%SRC_DIR%\Svn;%SRC_DIR%\Hg;%SRC_DIR%\Common
rem  --icon ..\Source\Windows\Resources\win_emacs.ico
pushd %SRC_DIR%\Scm
%PYTHON% -m win_app_packager build wb_scm_main.py --gui %DIST_DIR% --name "SCM Workbench" --verbose
    if errorlevel 1 goto :eof
popd >null

mkdir %DIST_DIR%\plugins\platforms
xcopy /q %BUILDER_QTDIR%\msvc2015_64\plugins\platforms\qwindows.dll %DIST_DIR%\plugins\platforms
    if errorlevel 1 goto :eof

mkdir %DIST_DIR%\plugins\imageformats
xcopy /q %BUILDER_QTDIR%\msvc2015_64\plugins\imageformats\*.dll %DIST_DIR%\plugins\imageformats
    if errorlevel 1 goto :eof
del /q %DIST_DIR%\plugins\imageformats\*d.dll

mkdir %DIST_DIR%\plugins\iconengins
xcopy /q %BUILDER_QTDIR%\msvc2015_64\plugins\iconengins\*.dll %DIST_DIR%\plugins\iconengins
    if errorlevel 1 goto :eof

echo Info: build-app.cmd done
endlocal
