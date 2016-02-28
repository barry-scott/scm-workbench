setlocal 
set BUILDER_START_DIR=
set BUILDER_TOP_DIR=
set BUILDROOT_DIR=
set __CMD_INIT_RUN__=

%PYTHON% wb_git_main.py %* 
endlocal 
