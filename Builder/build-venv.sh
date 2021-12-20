#!/bin/bash
set -e

if ! which colour-print >/dev/null
then
    function colour-print {
        echo "$@"
    }
fi

case "$(uname)" in
Darwin)
    requirements_file=macos-requirements.txt
    ;;

*)
    colour-print "<>error Error:<> not support on $(uanme)"
    exit 1
    ;;
esac

colour-print "<>info Info:<> Clean up"
rm -rf tmp/venv

colour-print "<>info Info:<> Create venv for ${PYTHON}"
${PYTHON} -m venv tmp/venv

colour-print "<>info Info:<> Install requirements"

tmp/venv/bin/python -m pip install --upgrade pip setuptools
tmp/venv/bin/python -m pip install -r ${requirements_file}
tmp/venv/bin/python -m pip list

colour-print "<>info Info: <> Install pysvn"
PYSVN_ORIGIN=$(${PYTHON} -c 'import os,pysvn;print(os.path.dirname(pysvn.__file__))')
cp -r ${PYSVN_ORIGIN} tmp/venv/lib/python${PYTHON_VERSION}/site-packages/
tmp/venv/bin/python -c 'import pysvn;print( "Info: PySVN %r SVN %r" % (pysvn.version, pysvn.svn_version) )'
