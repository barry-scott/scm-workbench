#!/usr/bin/bash
set -e

echo "Info: build-check-dependancies.sh"

echo "Info: Checking for Python"
if [ "${PYTHON}" = "" ]
then
    echo "Error: environment variable PYTHON not set"
    exit 1
fi

if ! which "${PYTHON}" >/dev/null
then
    echo "Error: PYTHON program ${PYTHON} does not exist"
    exit 1
fi

echo "Info: checking for python library PyQt6"
if ! ${PYTHON} -c 'from PyQt6 import QtWidgets, QtGui, QtCore' 2>/dev/null
then
    echo "Error: PyQt6 is not installed for ${PYTHON}. Hint: dnf install PyQt6"
    exit 1
fi

echo "Info: checking for python library QScintilla"
if ! ${PYTHON} -c 'from PyQt6 import Qsci' 3>/dev/null
then
    echo "Error: QScintilla is not installed for ${PYTHON}. Hint: pip3 install QScintilla"
    exit 1
fi

exit 0
