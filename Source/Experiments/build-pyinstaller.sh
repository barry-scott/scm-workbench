#!/bin/bash

echo "Info: Cleanup"
rm -rf tmp.pyinstaller
mkdir tmp.pyinstaller
echo "Info: setup venv"
python3.10 -m venv tmp.pyinstaller/venv
tmp.pyinstaller/venv/bin/python -m pip install --upgrade pip setuptools wheel
tmp.pyinstaller/venv/bin/python -m pip install PyQt5 pyinstaller
tmp.pyinstaller/venv/bin/python -m pip list

echo "Info: Test gui_test.py from command line"
#tmp.pyinstaller/venv/bin/python gui_test.py

echo "Info: Build gui_test.py into an App"
tmp.pyinstaller/venv/bin/pyinstaller \
    --windowed \
    --distpath tmp.pyinstaller/dist \
    --workpath tmp.pyinstaller/work \
    --specpath tmp.pyinstaller/spec \
        gui_test.py \
            2>&1 | tee tmp.pyinstaller/pyinstaller.log

echo "Info: Test gui_test.py as App bundle"
open tmp.pyinstaller/dist/gui_test.app
