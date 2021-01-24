@echo off
setlocal

if "%1" == "" goto :error

set requirements_file=%1-requirements.txt

%PYTHON% -m colour_text "<>info Info:<> Clean up"
if exist venv.tmp rmdir /s /q venv.tmp

%PYTHON% -m colour_text "<>info Info:<> Create venv for %PYTHON%"
%PYTHON% -m venv venv.tmp

%PYTHON% -m colour_text "<>info Info:<> Install requirements"

venv.tmp\Scripts\python.exe -m pip install --upgrade pip setuptools
venv.tmp\Scripts\python.exe -m pip install -r %requirements_file%
venv.tmp\Scripts\python.exe -m pip list
goto :eof

:error
    %PYTHON% -m colour_text "<>error Error: missing %%1 os arg<>"
endlocal
