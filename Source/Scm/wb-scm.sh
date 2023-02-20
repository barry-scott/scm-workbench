#!/bin/bash
set -e
set -x
export SCM_WORKBENCH_STDOUT_LOG=$(tty)

if [ "${BUILDER_TOP_DIR}" = "" ]
then
    BUILDER_TOP_DIR=$( cd ../..; pwd )
fi

SCMPYTHONPATH=\
${BUILDER_TOP_DIR}/Source/Scm:\
${BUILDER_TOP_DIR}/Source/Git:\
${BUILDER_TOP_DIR}/Source/Hg:\
${BUILDER_TOP_DIR}/Source/Svn:\
${BUILDER_TOP_DIR}/Source/Common:\
${BUILDER_TOP_DIR}/Builder/tmp/ROOT/usr/share/scm-workbench/lib
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
echo PYTHONPATH $PYTHONPATH

pushd ..
make -f linux.mak clean
make -f linux.mak
popd

PROG="scm-workbench-git-callback"

pwd

case "$( uname )" in
Darwin)
    echo "#!/usr/bin/python3" >"${PROG}"
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
    gdb -x .gdbinit ${BUILDER_TOP_DIR}/Builder/tmp/venv/bin/python

else
    case "$( uname )" in
    Darwin)
        # run Python with the path that it has when started by macOS as an App
        PATH=/usr/bin:/bin:/usr/sbin:/sbin ${BUILDER_TOP_DIR}/Builder/tmp/venv/bin/python wb_scm_main.py "$@"
        ;;
    *)
        $PWD/wb_scm_main.py "$@"
        ;;
    esac
fi
