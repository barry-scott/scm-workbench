setlocal 
set PYTHONPATH=%BUILDER_TOP_DIR%\Source\Scm;%BUILDER_TOP_DIR%\Source\Common;%BUILDER_TOP_DIR%\Source\Git;%BUILDER_TOP_DIR%\Source\Svn;%BUILDER_TOP_DIR%\Source\Hg

set BUILDER_START_DIR=
set BUILDER_TOP_DIR=
set BUILDROOT_DIR=
set __CMD_INIT_RUN__=

echo PYTHONPATH %PYTHONPATH%
%PYTHON% wb_scm_main.py %* 
endlocal 
