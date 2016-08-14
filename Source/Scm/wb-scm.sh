#!/bin/bash -x
export SCM_WORKBENCH_STDOUT_LOG=$(tty)

if [ "${BUILDER_TOP_DIR}" = "" ]
then
    BUILDER_TOP_DIR=$( cd ../..; pwd )
fi

SCMPYTHONPATH=${BUILDER_TOP_DIR}/Source/Scm:${BUILDER_TOP_DIR}/Source/Git:${BUILDER_TOP_DIR}/Source/Hg:${BUILDER_TOP_DIR}/Source/Svn:${BUILDER_TOP_DIR}/Source/Common

# for override libraries
OVERRIDE_PYTHONPATH=~/wc/git/GitPython

for PART in "${SCMPYTHONPATH}" "${OVERRIDE_PYTHONPATH}"
do
    if [ "${PART}" != "" ]
    then
        if [ "$PYTHONPATH" = "" ]
        then
            export PYTHONPATH="${PART}"
        else
            export PYTHONPATH="${PART}:${PYTHONPATH}"
        fi
    fi
done

PYTHON=${PYTHON:-python3}
BASENAME=$( basename ${PYTHON} )
SUFFIX=${BASENAME#python*}
DIRNAME=$( dirname ${PYTHON} )

if [ "${DIRNAME}" != "" ]
then
    DIRNAME=${DIRNAME}/
fi
PYTHONW=${DIRNAME}pythonw${SUFFIX}

pushd ../Common
make -f linux.mak clean
make -f linux.mak
popd >/dev/null

make -f linux.mak clean
make -f linux.mak

if [ "$1" = "--gdb" ]
then
    shift

    echo "set args wb_scm_main.py $*" >.gdbinit
    echo "echo gdbinit loaded\\n" >>.gdbinit
    gdb -x .gdbinit ${PYTHON}

else
    if [ -e ${PYTHONW} ]
    then
        ${PYTHONW} wb_scm_main.py $*
    else
        ${PYTHON} wb_scm_main.py $*
    fi
fi
