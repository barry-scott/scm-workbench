#!/bin/bash

colour-print "<>info Info: <> Clean up"
rm -rf venv.tmp

colour-print "<>info Info: <> Create venv for $PYTHON"
$PYTHON -m venv venv.tmp

colour-print "<>info Info: <> Install requirements"

venv.tmp/bin/python -m pip install --upgrade pip setuptools
venv.tmp/bin/python -m pip install -r requirements.txt
venv.tmp/bin/python -m pip list

colour-print "<>info Info: <> Install pysvn"
PYSVN_ORIGIN=$($PYTHON -c 'import os,pysvn;print(os.path.dirname(pysvn.__file__))')
cp -r ${PYSVN_ORIGIN} venv.tmp/lib/python${PYTHON_VERSION}/site-packages/
./venv.tmp/bin/python -c 'import pysvn;print( "Info: PySVN %r SVN %r" % (pysvn.version, pysvn.svn_version) )'
