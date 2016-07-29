@set __e=%1
@if "%1" == "" set __e=off
@echo %__e%
rem builder_custom_init

set VC_VER=14.0
set BUILDER_CFG_PLATFORM=Win64
set BUILDER_CFG_BUILD_TYPE=Release
set PYTHON_VERSION=3.5
set PYTHON_FILE_VERSION=35
set BUILDER_QTDIR=c:\Qt\Qt5.6.0\5.6

rem if Win64 then setup path to include the 64bit CL.exe
rem when called in place this can fork bomb (lots of CMD.exe in task manager)
call "C:\Program Files (x86)\Microsoft Visual Studio %VC_VER%\VC\bin\amd64\vcvars64.bat"
@echo %__e%

set PYTHON=c:\python%PYTHON_FILE_VERSION%.%BUILDER_CFG_PLATFORM%\python
PATH c:\python%PYTHON_FILE_VERSION%.%BUILDER_CFG_PLATFORM%;%PATH%
%PYTHON% -c "import sys;print( 'Python:', sys.version )"
