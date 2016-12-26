#!/bin/bash
set -e
echo "Info: build-app.sh"
SRC_DIR=${BUILDER_TOP_DIR}/Source
KIT_DIR=${BUILDER_TOP_DIR}/Kit/macOS

PYSVN_PATH=$( ${PYTHON} -c 'import pysvn;print(pysvn.__path__[0])' )
PY_VER=$( ${PYTHON} -c 'import sys;print( "%d.%d" % (sys.version_info.major, sys.version_info.minor) )' )
DIST_DIR=app.tmp

rm -rf ${DIST_DIR}
mkdir -p ${DIST_DIR}

pushd ${SRC_DIR}/Common
make -f linux.mak clean
make -f linux.mak
popd >/dev/null

pushd ${SRC_DIR}/Scm
make -f linux.mak clean
make -f linux.mak
popd >/dev/null

# wb_scm_version.py is bash compatible
. ${SRC_DIR}/Scm/wb_scm_version.py

mkdir -p ${DIST_DIR}/wb.iconset
sips -z 16 16     ${SRC_DIR}/wb.png --out ${DIST_DIR}/wb.iconset/icon_16x16.png
sips -z 32 32     ${SRC_DIR}/wb.png --out ${DIST_DIR}/wb.iconset/icon_16x16@2x.png
sips -z 32 32     ${SRC_DIR}/wb.png --out ${DIST_DIR}/wb.iconset/icon_32x32.png
sips -z 64 64     ${SRC_DIR}/wb.png --out ${DIST_DIR}/wb.iconset/icon_32x32@2x.png
sips -z 128 128   ${SRC_DIR}/wb.png --out ${DIST_DIR}/wb.iconset/icon_128x128.png
sips -z 256 256   ${SRC_DIR}/wb.png --out ${DIST_DIR}/wb.iconset/icon_128x128@2x.png
sips -z 256 256   ${SRC_DIR}/wb.png --out ${DIST_DIR}/wb.iconset/icon_256x256.png
sips -z 512 512   ${SRC_DIR}/wb.png --out ${DIST_DIR}/wb.iconset/icon_256x256@2x.png
sips -z 512 512   ${SRC_DIR}/wb.png --out ${DIST_DIR}/wb.iconset/icon_512x512.png
cp                ${SRC_DIR}/wb.png       ${DIST_DIR}/wb.iconset/icon_512x512@2x.png
iconutil -c icns ${DIST_DIR}/wb.iconset

export PYTHONPATH=${SRC_DIR}/Scm:${SRC_DIR}/Git:${SRC_DIR}/Svn:${SRC_DIR}/Hg:${SRC_DIR}/Common
${PYTHON} build-app-py2app-setup.py py2app --dist-dir ${DIST_DIR} --bdist-base ${DIST_DIR}/build --no-strip 2>&1 | tee py2app.log

pushd "${DIST_DIR}/SCM Workbench-Devel.app/Contents" >/dev/null

# copy all the installed PyQt5 files as py2app does not copy them all
cp -R \
    "/Library/Frameworks/Python.framework/Versions/${PY_VER}/lib/python${PY_VER}/site-packages/PyQt5" \
    "Resources/lib/python${PY_VER}/lib-dynload"

for LIBNAME in \
    QtCore \
    QtDBus \
    QtGui \
    QtPrintSupport \
    QtSvg \
    QtWidgets \
    QtMacExtras \
    ;
do
    echo "Info: framework used ${LIBNAME}"
done


#
#   add in the askpass client
#
PROG=Resources/scm-workbench-askpass
echo '#!/usr/bin/python2.7' >${PROG}
cat ${BUILDER_TOP_DIR}/Source/Git/wb_git_askpass_client_unix.py >>${PROG}
chmod +x ${PROG}
unset PROG

popd >/dev/null
echo "Info: build-app.sh done"
