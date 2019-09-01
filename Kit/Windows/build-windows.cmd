setlocal
call build-venv.cmd
    if errorlevel 1 goto :error
call build-extras.cmd
    if errorlevel 1 goto :error
call build-app.cmd
    if errorlevel 1 goto :error
call build-kit.cmd %1
    if errorlevel 1 goto :error
goto :eof
:error
    colour-print "<>error Error: Build failed<>"
endlocal
