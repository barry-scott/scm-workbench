#!/bin/bash
if [ "${BUILDER_TOP_DIR}" = "" ]
then
    BUILDER_TOP_DIR=$( cd ../..; pwd )
fi

SCMPYTHONPATH=${BUILDER_TOP_DIR}/Source/Scm:${BUILDER_TOP_DIR}/Source/Git:${BUILDER_TOP_DIR}/Source/Hg:${BUILDER_TOP_DIR}/Source/Svn:${BUILDER_TOP_DIR}/Source/Common

# for override libraries
OVERRIDE_PYTHONPATH_1=~/wc/git/GitPython
OVERRIDE_PYTHONPATH_2=~/wc/hg/hglib-setprotocol-patch
OVERRIDE_PYTHONPATH_2=~/wc/hg/hglib-prompt-patch

export MYPYPATH=/Library/Frameworks/Python.framework/Versions/3.5/lib/python3.5/site-packages

for PART in ${BUILDER_TOP_DIR}/Source/typelib "${SCMPYTHONPATH}" "${OVERRIDE_PYTHONPATH_1}" "${OVERRIDE_PYTHONPATH_2}"
do
    if [ "${PART}" != "" ]
    then
        if [ "${MYPYPATH}" = "" ]
        then
            export MYPYPATH="${PART}"
        else
            export MYPYPATH="${PART}:${MYPYPATH}"
        fi
    fi
done

PYTHON=${PYTHON:-python3}
PYTHON=$( which ${PYTHON} )

${PYTHON} -m mypy wb_scm_main.py | tee mypy.log
echo "Info: log file mypy.log ($( wc -l <mypy.log ))"
