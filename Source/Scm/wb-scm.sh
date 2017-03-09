#!/bin/bash -x
export SCM_WORKBENCH_STDOUT_LOG=$(tty)

if [ "${BUILDER_TOP_DIR}" = "" ]
then
    BUILDER_TOP_DIR=$( cd ../..; pwd )
fi

SCMPYTHONPATH=${BUILDER_TOP_DIR}/Source/Scm:${BUILDER_TOP_DIR}/Source/Git:${BUILDER_TOP_DIR}/Source/Hg:${BUILDER_TOP_DIR}/Source/Svn:${BUILDER_TOP_DIR}/Source/Common

# for override libraries
#OVERRIDE_PYTHONPATH_1=~/wc/git/GitPython
#OVERRIDE_PYTHONPATH_2=~/wc/hg/hglib-prompt-patch
#OVERRIDE_PYTHONPATH_2=~/wc/hg/hglib-setprotocol-patch

for PART in "${SCMPYTHONPATH}" "${OVERRIDE_PYTHONPATH_1}" "${OVERRIDE_PYTHONPATH_2}"
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
PYTHON=$( which ${PYTHON} )
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

PROG="scm-workbench-git-callback"

pwd

case "$( uname )" in
Darwin)
    echo "#!/usr/bin/python2.7" >"${PROG}"
    ;;

*)
    echo "#!$( which ${PYTHON} )" >"${PROG}"
    ;;
esac

cat ../Git/wb_git_callback_client_unix.py >>"${PROG}"
chmod +x "${PROG}"
unset PROG

if [ "$1" = "--gdb" ]
then
    shift

    echo "set args wb_scm_main.py $*" >.gdbinit
    echo "echo gdbinit loaded\\n" >>.gdbinit
    gdb -x .gdbinit ${PYTHON}

else
    # run Python with the path that it has when started by macOS as an App
    if [ -e ${PYTHONW} ]
    then
        PATH=/usr/bin:/bin:/usr/sbin:/sbin ${PYTHONW} wb_scm_main.py $*
    else
        PATH=/usr/bin:/bin:/usr/sbin:/sbin ${PYTHON} wb_scm_main.py $*
    fi
fi
