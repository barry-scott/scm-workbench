@echo off
setlocal
set SRC=%BUILDER_TOP_DIR%\Source\Common
set PYTHONPATH=%SRC%

pushd %BUILDER_TOP_DIR%\Source\Common
%PYTHON% make_wb_diff_images.py
popd

%PYTHON%  %SRC%\wb_diff_main.py "%1" "%2" "%3"
endlocal
