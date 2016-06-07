#!/bin/bash -x
export HG_WORKBENCH_STDOUT_LOG=$(tty)

if [ "${BUILDER_TOP_DIR}" = "" ]
then
    BUILDER_TOP_DIR=.
fi
if [ "$PYTHONPATH" = "" ]
then
	export PYTHONPATH=${BUILDER_TOP_DIR}/Source/Hg:${BUILDER_TOP_DIR}/Source/Common
else
	export PYTHONPATH=${BUILDER_TOP_DIR}/Source/Hg:${BUILDER_TOP_DIR}/Source/Common:$PYTHONPATH
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

    echo "set args wb_hg_main.py $*" >.gdbinit
    echo "echo gdbinit loaded\\n" >>.gdbinit
    gdb -x .gdbinit ${PYTHON}

else
    if [ -e ${PYTHONW} ]
    then
        ${PYTHONW} wb_hg_main.py $*
    else
        ${PYTHON} wb_hg_main.py $*
    fi
fi
