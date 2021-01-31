@echo on
setlocal
for %%f in (tmp\SCM-Workbench-*-setup.exe) do set KIT=%%f
dir %KIT%
copy %KIT% k:\ScmWorkbench\beta
endlocal
