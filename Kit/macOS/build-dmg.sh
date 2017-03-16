#!/bin/bash
set -e

echo "Info: build-dmg.sh - start"

# the .py is bash compatible
. ${BUILDER_TOP_DIR}/Source/Scm/wb_scm_version.py

export PKG_NAME=SCM-Workbench-${major}.${minor}.${patch}
export APP_PATH="dmg.tmp/${PKG_NAME}/${APP_NAME}.app"

MOUNT_POINT="/Volumes/${APP_NAME}"
if [ -e "${MOUNT_POINT}" ]
then
    echo "Info: umount old DMG"
    umount "${MOUNT_POINT}"
fi

rm -rf dmg.tmp
mkdir dmg.tmp
mkdir dmg.tmp/${PKG_NAME}

echo "Info: copy app"
cp -r "app.tmp/${APP_NAME}-Devel.app" "${APP_PATH}"
mv \
    "${APP_PATH}/Contents/MacOS/${APP_NAME}-Devel" \
    "${APP_PATH}/Contents/MacOS/${APP_NAME}"

echo "Info: Create DMG"
# use 2.7 version as 3.5 version does not work yet (confuses bytes and str)
PYTHONPATH=${BUILDER_TOP_DIR}/Source/Scm \
    /Library/Frameworks/Python.framework/Versions/2.7/bin/dmgbuild \
        --settings dmg_settings.py  \
        "${APP_NAME}" \
        dmg.tmp/${PKG_NAME}.dmg

if [ "$1" == "--install" ]
then
    open dmg.tmp/${PKG_NAME}.dmg
fi


echo "Info: build-dmg.sh - end"
