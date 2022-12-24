#!/bin/bash
set -e

if ! which colour-print >/dev/null
then
    function colour-print {
        echo "$@"
    }
fi

colour-print "<>info Info:<> build-linux.sh Builder - start"

colour-print "<>info Info:<> Checking for Python"

if [ "${PYTHON}" = "" ]
then
    colour-print "<>error Error: environment variable PYTHON not set<>"
    exit 1
fi

if ! which "${PYTHON}" >/dev/null
then
    colour-print "<>Error: PYTHON program ${PYTHON} does not exist<>"
    exit 1
fi

${PYTHON} ./build_scm_workbench.py --colour | ${PYTHON} -u build_tee.py build.log
colour-print "<>info Info:<> build-linux.sh Builder - end"
