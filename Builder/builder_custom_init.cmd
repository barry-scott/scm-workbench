@set __e=%1
@if "%1" == "" set __e=off
@echo %__e%
rem builder_custom_init

set BUILDER_CFG_PLATFORM=Win64
set BUILDER_CFG_BUILD_TYPE=Release
set PYTHON_VERSION=3.5
set PYTHON_FILE_VERSION=35

set PYTHON=c:\python%PYTHON_FILE_VERSION%.%BUILDER_CFG_PLATFORM%\python
PATH c:\python%PYTHON_FILE_VERSION%.%BUILDER_CFG_PLATFORM%;%PATH%
%PYTHON% -c "import sys;print( 'Python:', sys.version )"
