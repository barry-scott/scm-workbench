@echo off
setlocal
SCM-Workbench-0.9.3-setup.exe
for %%f in (.\SCM-Workbench-*-setup.exe) do set KIT=%%f
dir %KIT%
copy %KIT% k:\ScmWorkbench\beta
endlocal
