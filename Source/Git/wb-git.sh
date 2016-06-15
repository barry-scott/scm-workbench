#!/bin/bash -x
export GIT_WORKBENCH_STDOUT_LOG=$(tty)

if [ "${BUILDER_TOP_DIR}" = "" ]
then
    BUILDER_TOP_DIR=$( cd ../..; pwd )
fi
if [ "$PYTHONPATH" = "" ]
then
	export PYTHONPATH=${BUILDER_TOP_DIR}/Source/Git:${BUILDER_TOP_DIR}/Source/Common
else
	export PYTHONPATH=${BUILDER_TOP_DIR}/Source/Git:${BUILDER_TOP_DIR}/Source/Common:$PYTHONPATH
fi

PYTHON=${PYTHON:-python3}
BASENAME=$( basename ${PYTHON} )
SUFFIX=${BASENAME#python*}
DIRNAME=$( dirname ${PYTHON} )

if [ "${DIRNAME}" != "" ]
then
    DIRNAME=${DIRNAME}/
fi
PYTHONW=${DIRNAME}pythonw${SUFFIX}

make -f linux.mak

if [ "$1" = "--gdb" ]
then
    shift

    echo "set args wb_git_main.py $*" >.gdbinit
    echo "echo gdbinit loaded\\n" >>.gdbinit
    gdb -x .gdbinit ${PYTHON}

else
    if [ -e ${PYTHONW} ]
    then
        ${PYTHONW} wb_git_main.py $*
    else
        ${PYTHON} wb_git_main.py $*
    fi
fi
