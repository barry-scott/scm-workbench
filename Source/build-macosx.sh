#!/bin/bash
set -e

VPYTHON=${BUILDER_TOP_DIR}/Builder/tmp/venv/bin/python
if [ ! -e ${VPYTHON} ]
then
    echo "Error: venv python not found - ${VPYTHON}"
    exit 1
fi

function colour-print {
    ${VPYTHON} -m colour_text "$@"
}

colour-print "<>info Info:<> build-macosx.sh - start"

BUILDER_DIR=${BUILDER_TOP_DIR}/Builder
SRC_DIR=${BUILDER_TOP_DIR}/Source
DOCS_DIR=${BUILDER_TOP_DIR}/Docs

TMP_SRC=${BUILDER_TOP_DIR}/Builder/tmp/Source
rm -rf ${TMP_SRC}
mkdir ${TMP_SRC}

${VPYTHON} ${SRC_DIR}/make_wb_scm_version.py \
    ${BUILDER_TOP_DIR}/Builder/version.dat \
    ${TMP_SRC}/wb_scm_version.py

${VPYTHON} make_wb_scm_images.py \
    ${TMP_SRC}/wb_scm_images.py

# happens to work as a shell source
. ${TMP_SRC}/wb_scm_version.py

if [ "$1" = "--package" ]
then
    export DIST_DIR=${BUILDER_TOP_DIR}/Builder/tmp/app
    PY2APP_OPT='--package'

else
    export DIST_DIR=dist
    PY2APP_OPT=''
    APP_NAME=${APP_NAME}-Devel
fi

PY_VER=$( ${VPYTHON} -c 'import sys;print( "%d.%d" % (sys.version_info.major, sys.version_info.minor) )' )

rm -rf ${DIST_DIR}
mkdir -p ${DIST_DIR}

colour-print "<>info Info:<> Creating Application bundle"

# assume that pysvn is install outside of the VENV
PYSVN_PATH=$( ${PYTHON} -c 'import pysvn;print(pysvn.__path__[0])' )

# make translation PO files
pushd ${SRC_DIR} >/dev/null
make -f linux.mak clean
make -f linux.mak
popd >/dev/null

# wb_scm_version.py is bash compatible
. ${TMP_SRC}/wb_scm_version.py

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

export PYTHONPATH=${TMP_SRC}:${SRC_DIR}/Scm:${SRC_DIR}/Git:${SRC_DIR}/Svn:${SRC_DIR}/Hg:${SRC_DIR}/Common

# true = pyinstall, false = py2app
if true
then
    # true = use wb-scm-pyinstall.spec, false = make a new one
    if true
    then
        ${BUILDER_TOP_DIR}/Builder/tmp/venv/bin/pyinstaller \
            --distpath ${DIST_DIR} \
                wb-scm-pyinstaller.spec
    else
        ${BUILDER_TOP_DIR}/Builder/tmp/venv/bin/pyinstaller \
            --log-level INFO \
            --distpath ${DIST_DIR} \
            --name "SCM Workbench" \
            --paths ${PYTHONPATH} \
            --windowed \
            --icon wb.icns \
            --osx-bundle-identifier ${APP_ID} \
                Scm/wb_scm_main.py
    fi

else
    ${BUILDER_DIR}/tmp/venv/bin/python \
        ${SRC_DIR}/build_macos_py2app_setup.py ${PY2APP_OPT} \
            py2app --dist-dir ${DIST_DIR} --bdist-base ${DIST_DIR}/build --no-strip \
                2>&1 | tee ${BUILDER_DIR}/tmp/py2app.log
fi

pushd "${DIST_DIR}/${APP_NAME}.app/Contents" >/dev/null

# py2app corrupts the dylibs - macOS report they are truncated
# replace with the original versions
cp ${PYSVN_PATH}/*.dylib Frameworks
${VPYTHON} ${BUILDER_DIR}/build_fix_install_rpath.py fix Frameworks/libsvn*.dylib

#
#   Copy in the docs
#
${VPYTHON} ${DOCS_DIR}/build-docs.py Resources/Documentation

if false
then
# fixup 1. only keep the frameworks that we need, saving space
# Resources/lib/python3.N/lib-dynload/PyQt6 - QtXxx.so
mkdir \
    Resources/lib/python${PYTHON_VERSION}/PyQt6/tmp
mv \
    Resources/lib/python${PYTHON_VERSION}/PyQt6/Qt?*.so \
    Resources/lib/python${PYTHON_VERSION}/PyQt6/tmp

# Resources/lib/python3.N/PyQt6/Qt/lib - QtXxx.framework
mkdir \
    Resources/lib/python${PYTHON_VERSION}/PyQt6/Qt/lib/tmp
mv \
    Resources/lib/python${PYTHON_VERSION}/PyQt6/Qt/lib/Qt*.framework \
    Resources/lib/python${PYTHON_VERSION}/PyQt6/Qt/lib/tmp

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
            Resources/lib/python${PYTHON_VERSION}/PyQt6/tmp/${LIBNAME}.so \
            Resources/lib/python${PYTHON_VERSION}/PyQt6
    mv \
        Resources/lib/python${PYTHON_VERSION}/PyQt6/Qt/lib/tmp/${LIBNAME}.framework \
        Resources/lib/python${PYTHON_VERSION}/PyQt6/Qt/lib
done

# fixup 2. remove the unused frameworks
rm -rf Resources/lib/python${PYTHON_VERSION}/PyQt6/tmp
rm -rf Resources/lib/python${PYTHON_VERSION}/PyQt6/Qt/lib/tmp

# fixup 3. remove qml stuff
rm -rf Resources/lib/python${PYTHON_VERSION}/PyQt6/Qt/qml
rm -rf Resources/lib/python${PYTHON_VERSION}/PyQt6/Qt/translations
rm -rf Resources/lib/python${PYTHON_VERSION}/PyQt6/Qt/qsci
fi

#
#   add in the git-callback client
#
PROG=Resources/scm-workbench-git-callback
echo '#!/usr/bin/python3' >${PROG}
cat ${BUILDER_TOP_DIR}/Source/Git/wb_git_callback_client_unix.py >>${PROG}
chmod +x ${PROG}
unset PROG

popd >/dev/null
echo "Info: build-app.sh done"
