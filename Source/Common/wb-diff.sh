#!/bin/bash -x
export SCM_WORKBENCH_STDOUT_LOG=$(tty)

if [ "${BUILDER_TOP_DIR}" = "" ]
then
    BUILDER_TOP_DIR=$( cd ../..; pwd )
fi

export PYTHONPATH=${BUILDER_TOP_DIR}/Source/Common

PYTHON=${PYTHON:-python3}
PYTHON=$( which ${PYTHON} )
BASENAME=$( basename ${PYTHON} )
SUFFIX=${BASENAME#python*}
DIRNAME=$( dirname ${PYTHON} )

if [ "${DIRNAME}" != "" ]
then
    DIRNAME=${DIRNAME}/
fi
PYTHONW=${DIRNAME}pythonw${SUFFIX}

pushd ${BUILDER_TOP_DIR}/Source/Common
make -f linux.mak clean
make -f linux.mak
popd


if [ "$1" = "--gdb" ]
then
    shift

    echo "set args wb_scm_main.py $*" >.gdbinit
    echo "echo gdbinit loaded\\n" >>.gdbinit
    gdb -x .gdbinit ${PYTHON}

else
    case "$( uname )" in
    Darwin)
        # run Python with the path that it has when started by macOS as an App
        if [ -e ${PYTHONW} ]
        then
            PATH=/usr/bin:/bin:/usr/sbin:/sbin ${PYTHONW} wb_diff_main.py $*
        else
            PATH=/usr/bin:/bin:/usr/sbin:/sbin ${PYTHON} wb_diff_main.py $*
        fi
        ;;
    *)
        if [ "$1" == "-u" ]
        then
            shift 1
        fi
        ${PYTHON} ${BUILDER_TOP_DIR}/Source/Common/wb_diff_main.py "$@"
        ;;
    esac
fi
