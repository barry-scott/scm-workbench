#!/bin/bash
KIT_DIR="${PWD}"
BUILD="${KIT_DIR}/BUILD"
BUILDROOT="${KIT_DIR}/BUILDROOT"

./build-rpms.sh --tarball

echo BUILD ${BUILD}

rm -rf ${BUILD}
mkdir ${BUILD}

echo BUILDROOT ${BUILD}

rm -rf ${BUILDROOT}
mkdir ${BUILDROOT}

cd ${BUILD}
tar xf ../tmp/scm-workbench*.tar.gz
ls -l
cd scm-workbench-*
. ~/bin/builder_init
${KIT_DIR}/build-install-tree.sh \
    "${BUILDROOT}" \
    "$(rpm --eval %{_bindir})" \
    "$(rpm --eval %{_datarootdir})/scm-workbench" \
    "$(rpm --eval %{_mandir})/man1" \
    "$(rpm --eval %{_datarootdir})/doc/scm-workbench" \
    "$(rpm --eval %{_datarootdir})/applications"
