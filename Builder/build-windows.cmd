@echo off
setlocal
if "%BUILDER_TOP_DIR%" == "" (
    echo "Error: BUILDER_TOP_DIR is not set. Hint: run builder_custom_init.cmd"
    goto :eof
)
if "%BUILDER_CFG_PLATFORM%" == "" (
    echo "Error: BUILDER_CFG_PLATFORM is not set. Hint: fix builder_custom_init.cmd to set it."
    goto :eof
)

if "%PYTHON%" == "" (
    echo "error Error: PYTHON is not set. Hint: fix builder_custom_init.cmd to set it."
    goto :eof
)

if exist tmp rmdir /s /q tmp
mkdir tmp
mkdir tmp\app

if not "%1" == "--no-venv"  call build-venv.cmd windows

set VPYTHON=%CD%\venv.tmp\Scripts\python.exe
if "%1" == "--enable-debug" set BUILD_OPT=--enable-debug
%VPYTHON% build_scm_workbench.py --colour --vcredist=k:\subversion %BUILD_OPT% 2>&1 | "%PYTHON%" -u build_tee.py build.log

if "%1" == "--install" for %%f in (tmp\scm-workbench-*-setup.exe) do start /wait %%f
endlocal
