@echo off
setlocal

if "%1" == "" goto :error

set requirements_file=%1-requirements.txt

%PYTHON% -m colour_text "<>info Info:<> Clean up"
if exist venv.tmp rmdir /s /q venv.tmp

%PYTHON% -m colour_text "<>info Info:<> Create venv for %PYTHON%"
%PYTHON% -m venv venv.tmp

%PYTHON% -m colour_text "<>info Info:<> Install requirements"

venv.tmp\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
venv.tmp\Scripts\python.exe -m pip install -r %requirements_file%
venv.tmp\Scripts\python.exe -m pip list

%PYTHON% -m colour_text "<>info Info:<> Install pysvn"
%PYTHON% -c "import pysvn,os;print(os.path.dirname(pysvn.__file__))" >pysvn.tmp
for /f %%x in (pysvn.tmp) do xcopy /s /q %%x venv.tmp\lib\site-packages\pysvn\
del pysvn.tmp

goto :eof

:error
    %PYTHON% -m colour_text "<>error Error: missing %%1 os arg<>"
endlocal
