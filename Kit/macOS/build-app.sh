#!/bin/bash
set -e
echo "Info: build-app.sh"
SRC_DIR=${BUILDER_TOP_DIR}/Source
KIT_DIR=${BUILDER_TOP_DIR}/Kit/macOS

PYSVN_PATH=$( ${PYTHON} -c 'import pysvn;print(pysvn.__path__[0])' )
PY_VER=$( ${PYTHON} -c 'import sys;print( "%d.%d" % (sys.version_info.major, sys.version_info.minor) )' )
DIST_DIR=app.tmp

rm -rf build
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
${PYTHON} build-app-py2app-setup.py py2app --dist-dir ${DIST_DIR} --no-strip 2>&1 | tee py2app.log

# py2app copies the wrong dylibs for pysvn
cp \
    "${PYSVN_PATH}"/*.dylib \
    "${DIST_DIR}/SCM Workbench-Devel.app/Contents/Frameworks"

pushd "${DIST_DIR}/SCM Workbench-Devel.app/Contents" >/dev/null

${PYTHON} ${KIT_DIR}/build_fix_install_rpath.py fix Resources/lib/python${PY_VER}/lib-dynload/PyQt5/*.so

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
    echo "Info: Copy framework ${LIBNAME}"
    cp -R \
        "${BUILDER_QTDIR}/clang_64/lib/${LIBNAME}.framework" \
        "Frameworks"

    ${PYTHON} ${KIT_DIR}/build_fix_install_rpath.py show "Frameworks/${LIBNAME}.framework/${LIBNAME}"
done

echo "Info: remove Headers links"
find "Frameworks" -type l -name 'Headers' -exec rm -f {} ';'
echo "Info: remove Headers dirs"
find -d "Frameworks" -type d -name 'Headers' -exec rm -rf {} ';'

for PLUGIN in \
    imageformats/libqdds.dylib \
    imageformats/libqgif.dylib \
    imageformats/libqicns.dylib \
    imageformats/libqico.dylib \
    imageformats/libqjpeg.dylib \
    imageformats/libqsvg.dylib \
    imageformats/libqtga.dylib \
    imageformats/libqtiff.dylib \
    imageformats/libqwbmp.dylib \
    imageformats/libqwebp.dylib \
    platforms/libqcocoa.dylib \
    ;
do
    echo "Info: Copy plugin ${PLUGIN}"
    TARGET_DIR=$( dirname "Resources/plugins/${PLUGIN}" )
    mkdir -p "${TARGET_DIR}"
    cp \
        "${BUILDER_QTDIR}/clang_64/plugins/${PLUGIN}" \
        "${TARGET_DIR}"

    ${PYTHON} ${KIT_DIR}/build_fix_install_rpath.py fix "Resources/plugins/${PLUGIN}"
done

popd >/dev/null
echo "Info: build-app.sh done"
