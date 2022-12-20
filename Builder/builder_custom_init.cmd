@set __e=%1
@if "%1" == "" set __e=off
@echo %__e%
rem builder_custom_init

set BUILDER_CFG_PLATFORM=Win64
set BUILDER_CFG_BUILD_TYPE=Release
set PYTHON_VERSION=3.11

py -%PYTHON_VERSION%-64 -c "import sys;print('set PYTHON=' + sys.executable)" >%TEMP%\__tmp__.cmd
call %TEMP%\__tmp__.cmd
del %TEMP%\__tmp__.cmd
echo Python %PYTHON_VERSION% found in %PYTHON%
"%PYTHON%" -c "import sys;print( 'Python:', sys.version )"
