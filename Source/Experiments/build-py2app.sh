#!/bin/bash

echo "Info: Cleanup"
rm -rf tmp.py2app
mkdir tmp.py2app
echo "Info: setup venv"
python3.10 -m venv tmp.py2app/venv
tmp.py2app/venv/bin/python -m pip install --upgrade pip setuptools wheel
tmp.py2app/venv/bin/python -m pip install PyQt5 py2app
tmp.py2app/venv/bin/python -m pip list

echo "Info: Test gui_test.py from command line"
tmp.py2app/venv/bin/python gui_test.py

echo "Info: Build gui_test.py into an App"
tmp.py2app/venv/bin/python \
    gui_setup.py \
        py2app --dist-dir tmp.py2app/app --bdist-base tmp.py2app/build --no-strip \
            2>&1 | tee tmp.py2app/py2app.log


echo "Info: Test gui_test.py as App bundle"
open tmp.py2app/app/gui_test.app
