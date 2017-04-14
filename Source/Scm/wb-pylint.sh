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

for PART in "${SCMPYTHONPATH}" "${OVERRIDE_PYTHONPATH_1}" "${OVERRIDE_PYTHONPATH_2}"
do
    if [ "${PART}" != "" ]
    then
        if [ "${PYTHONPATH}" = "" ]
        then
            export PYTHONPATH="${PART}"
        else
            export PYTHONPATH="${PART}:${PYTHONPATH}"
        fi
    fi
done

make -f linux.mak
pushd ../Common
make -f linux.mak
popd

python3-pylint --rcfile pylintrc wb_*.py ../Common/wb*.py ../Git/wb*.py ../Svn/wb*.py ../Hg/wb*.py | tee pylint.log
echo "Info: log file pylint.log ($( wc -l <pylint.log ))"
