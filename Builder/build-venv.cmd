@echo off
setlocal

set requirements_file=windows-requirements.txt

"%PYTHON%" -m colour_text "<>info Info:<> Clean up"
if exist venv.tmp rmdir /s /q venv.tmp

"%PYTHON%" -m colour_text "<>info Info:<> Create venv for %PYTHON%"
"%PYTHON%" -m venv venv.tmp

"%PYTHON%" -m colour_text "<>info Info:<> Install requirements"

venv.tmp\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
venv.tmp\Scripts\python.exe -m pip install -r %requirements_file%
venv.tmp\Scripts\python.exe -m pip list

"%PYTHON%" -m colour_text "<>info Info:<> Install pysvn"
"%PYTHON%" -c "import pysvn,os;print('set PYSVN_DIR='+os.path.dirname(pysvn.__file__))" >%TEMP%\__tmp__.cmd
call %TEMP%\__tmp__.cmd
del %TEMP%\__tmp__.cmd

xcopy /s /q "%PYSVN_DIR%" venv.tmp\lib\site-packages\pysvn\
endlocal
