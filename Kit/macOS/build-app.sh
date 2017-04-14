#!/bin/bash
set -e
echo "Info: build-app.sh"
DOCS_DIR=${BUILDER_TOP_DIR:? run builder_init}/Docs
SRC_DIR=${BUILDER_TOP_DIR}/Source
KIT_DIR=${BUILDER_TOP_DIR}/Kit/macOS

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

#
#   Copy in the docs
#
${DOCS_DIR}/build-docs.py Resources/Documentation

# fixup 1. only keep the frameworks that we need, saving space
# Resources/lib/python3.N/lib-dynload/PyQt5 - QtXxx.so
mkdir \
    Resources/lib/python${PYTHON_VERSION}/PyQt5/tmp
mv \
    Resources/lib/python${PYTHON_VERSION}/PyQt5/Qt?*.so \
    Resources/lib/python${PYTHON_VERSION}/PyQt5/tmp

# Resources/lib/python3.N/PyQt5/Qt/lib - QtXxx.framework
mkdir \
    Resources/lib/python${PYTHON_VERSION}/PyQt5/Qt/lib/tmp
mv \
    Resources/lib/python${PYTHON_VERSION}/PyQt5/Qt/lib/Qt*.framework \
    Resources/lib/python${PYTHON_VERSION}/PyQt5/Qt/lib/tmp

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
    mv \
            Resources/lib/python${PYTHON_VERSION}/PyQt5/tmp/${LIBNAME}.so \
            Resources/lib/python${PYTHON_VERSION}/PyQt5
    mv \
        Resources/lib/python${PYTHON_VERSION}/PyQt5/Qt/lib/tmp/${LIBNAME}.framework \
        Resources/lib/python${PYTHON_VERSION}/PyQt5/Qt/lib
done

# fixup 2. remove the unused frameworks
rm -rf Resources/lib/python${PYTHON_VERSION}/PyQt5/tmp
rm -rf Resources/lib/python${PYTHON_VERSION}/PyQt5/Qt/lib/tmp

# fixup 3. remove qml stuff
rm -rf Resources/lib/python${PYTHON_VERSION}/PyQt5/Qt/qml
rm -rf Resources/lib/python${PYTHON_VERSION}/PyQt5/Qt/translations
rm -rf Resources/lib/python${PYTHON_VERSION}/PyQt5/Qt/qsci

#
#   add in the git-callback client
#
PROG=Resources/scm-workbench-git-callback
echo '#!/usr/bin/python2.7' >${PROG}
cat ${BUILDER_TOP_DIR}/Source/Git/wb_git_callback_client_unix.py >>${PROG}
chmod +x ${PROG}
unset PROG

popd >/dev/null
echo "Info: build-app.sh done"
