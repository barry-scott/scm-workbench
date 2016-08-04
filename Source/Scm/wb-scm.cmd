setlocal 
if "%BUILDER_TOP_DIR%" == "" (
    echo Error: BUILDER_TOP_DIR is not set
    goto :eof
)
set PYTHONPATH=%BUILDER_TOP_DIR%\Source\Scm;%BUILDER_TOP_DIR%\Source\Common;%BUILDER_TOP_DIR%\Source\Git;%BUILDER_TOP_DIR%\Source\Svn;%BUILDER_TOP_DIR%\Source\Hg

cd ..\Common
%PYTHON% make_wb_diff_images.py

cd ..\Scm
nmake -f windows.mak clean
nmake -f windows.mak all

set BUILDER_START_DIR=
set BUILDER_TOP_DIR=
set BUILDROOT_DIR=

echo PYTHONPATH %PYTHONPATH%
%PYTHON% wb_scm_main.py %* 
endlocal
