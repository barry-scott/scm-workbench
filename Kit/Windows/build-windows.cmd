setlocal
call %PYTHON% setup_kit_files.py %BUILDER_CFG_PLATFORM% %VC_VER%
call "c:\Program Files (x86)\Inno Setup 5\ISCC.exe" tmp\bemacs.iss
call tmp\setup_copy.cmd
endlocal
