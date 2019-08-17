@echo off
setlocal
set PYTHONPATH=%BUILDER_TOP_DIR%\Source\Scm
if exist tmp rmdir /s /q setup.tmp
mkdir setup.tmp
call %PYTHON% setup_kit_files.py %BUILDER_CFG_PLATFORM% %VC_VER%
    if errorlevel 1 goto :eof
call "c:\Program Files (x86)\Inno Setup 5\ISCC.exe" /q setup.tmp\scm-workbench.iss
    if errorlevel 1 goto :eof
call setup.tmp\setup_copy.cmd %1
endlocal
