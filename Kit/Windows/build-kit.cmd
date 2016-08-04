setlocal
set PYTHONPATH=%BUILDER_TOP_DIR%\Source\Scm
if exist tmp rmdir /s /q tmp
mkdir tmp
call %PYTHON% setup_kit_files.py %BUILDER_CFG_PLATFORM% %VC_VER%
call "c:\Program Files (x86)\Inno Setup 5\ISCC.exe" tmp\scm-workbench.iss
call tmp\setup_copy.cmd
endlocal
