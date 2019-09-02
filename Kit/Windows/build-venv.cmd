@echo off
@setlocal
colour-print "<>info Info: <> Clean up"
if exist venv.tmp rmdir /s /q venv.tmp
colour-print "<>info Info: <> Create venv"
%PYTHON% -m venv venv.tmp
colour-print "<>info Info: <> Install requirements"
venv.tmp\scripts\python -m pip install -r requirements.txt
venv.tmp\scripts\python -m pip list

colour-print "<>info Info: <> Install pysvn"
xcopy /s /q C:\Python37.win64\lib\site-packages\pysvn venv.tmp\lib\site-packages\pysvn\

endlocal
