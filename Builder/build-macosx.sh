#!/bin/bash
set -e

if ! which colour-print >/dev/null
then
    function colour-print {
        echo "$@"
    }
fi

colour-print "<>info Info:<> build-macosx.sh Builder - start"

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

if [ -e /Volumes/SCM-Workbench-*.dmg ]
then
    colour-print "<>info Info:<> unmount old kit dmg"
    umount /Volumes/SCM-Workbench-*.dmg
fi

if [ "$1" != "--no-venv" ]
then
    ./build-venv.sh macos
fi

export PYTHON=${PWD}/tmp/venv/bin/python
${PYTHON} ./build_scm_workbench.py --colour | ${PYTHON} -u build_tee.py build.log

DMG=$( ls -1 tmp/dmg/*.dmg )

colour-print "<>info Info:<> DMG ${DMG}"
if [ "$1" = "--install" ]
then
    # macOS knows about these extra copies of the app
    # and will start all of them at the same time so delete
    rm -rf tmp/app
    rm -rf tmp/dmg/*.app
    open "${DMG}"
fi
colour-print "<>info Info:<> build-macosx.sh Builder - end"
