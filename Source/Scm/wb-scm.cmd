@echo off
setlocal 
if "%BUILDER_TOP_DIR%" == "" (
    echo Error: BUILDER_TOP_DIR is not set
    goto :eof
)
set PYTHONPATH=%BUILDER_TOP_DIR%\Source\Scm;%BUILDER_TOP_DIR%\Source\Common;%BUILDER_TOP_DIR%\Source\Git;%BUILDER_TOP_DIR%\Source\Svn;%BUILDER_TOP_DIR%\Source\Hg

cd ..\Common
%PYTHON% make_wb_diff_images.py
    if errorlevel 1 goto :eof

cd ..\Scm
nmake -f windows.mak clean
    if errorlevel 1 goto :eof
nmake -f windows.mak all
    if errorlevel 1 goto :eof

set BUILDER_START_DIR=
set BUILDER_TOP_DIR=
set BUILDROOT_DIR=

echo on
echo PYTHONPATH %PYTHONPATH%
%PYTHON% wb_scm_main.py %*
if errorlevel 1 echo Error: wb_scm_main exited with error
endlocal
