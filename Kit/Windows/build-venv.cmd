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
%PYTHON% -c "import pysvn,os;print(os.path.dirname(pysvn.__file__))" >pysvn.tmp
for /f %%x in (pysvn.tmp) do xcopy /s /q %%x venv.tmp\lib\site-packages\pysvn\

endlocal
