setlocal 
set PYTHONPATH=%BUILDER_TOP_DIR%\Source;%BUILDER_TOP_DIR%\Source\Common

set BUILDER_START_DIR=
set BUILDER_TOP_DIR=
set BUILDROOT_DIR=
set __CMD_INIT_RUN__=

echo PYTHONPATH %PYTHONPATH%
%PYTHON% wb_git_main.py %* 
endlocal 
