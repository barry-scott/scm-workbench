@set __e=%1
@if "%1" == "" set __e=off
@echo %__e%
rem builder_custom_init

set VC_VER=14.0
set BUILDER_CFG_PLATFORM=Win64
set BUILDER_CFG_BUILD_TYPE=Release
set PYTHON_VERSION=3.8

for /f "usebackq" %%X in (`py -%PYTHON_VERSION%-64 -c "import sys;print(sys.executable)"`) do set PYTHON=%%X
echo Python %PYTHON_VERSION% found in %PYTHON%
%PYTHON% -c "import sys;print( 'Python:', sys.version )"
