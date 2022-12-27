#!/bin/bash
#
#   script called from debian/rules make file
#
set -e

export DESTDIR="$1"
export BUILDER_TOP_DIR=$(pwd)

# figure out the explicit python executable
#version=$( /usr/bin/python3 -c 'import sys;print("%d.%d" % (sys.version_info.major, sys.version_info.minor))' )
#export PYTHON=/usr/bin/python${version}

export PYTHON=/usr/bin/python3

echo "Info: debian scm-workbench builder BUILDER_TOP_DIR ${BUILDER_TOP_DIR} DESTDIR ${DESTDIR} PYTHON ${PYTHON}"

cd Builder

./build-install-tree.sh \
    ${DESTDIR} \
    /usr/bin \
    /usr/share/scm-workbench \
    /usr/share/man/man1 \
    /usr/share/doc/scm-workbench \
    /usr/share/applications

find "${DESTDIR}" -name __pycache__ -print -ls
find "${DESTDIR}" -name __pycache__ -exec rm -rf {} ';'

for page in scm-workbench.1 scm-workbench-git-callback.1
do
    mkdir -p "${DESTDIR}/usr/share/man/man1"
    gzip -c "${BUILDER_TOP_DIR}/Kit/Fedora/${page}" > "${DESTDIR}/usr/share/man/man1/${page}.gz"
done

mkdir -p \
    "${DESTDIR}/usr/share/scm-workbench"
cp  "${BUILDER_TOP_DIR}/Source/wb.png" \
    "${DESTDIR}/usr/share/scm-workbench/org.barrys-emacs.scm-workbench.png"

mkdir -p \
    "${DESTDIR}/usr/share/applications"
cp  "${BUILDER_TOP_DIR}/Kit/Fedora/scm-workbench.desktop" \
    "${DESTDIR}/usr/share/applications/org.barrys-emacs.scm-workbench.desktop"
