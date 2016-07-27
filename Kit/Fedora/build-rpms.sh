#!/usr/bin/bash
#
#   build-rpms.sh
#
set -e

CMD="$1"

echo "Info: Creating source tarball"

KITNAME=scm-workbench

V=$( cat ${BUILDER_TOP_DIR}/Builder/version.dat )
rm -rf ${TMPDIR:-/tmp}/${NAME}-${V}

KIT_BASENAME=${KITNAME}-${V}

rm -rf tmp
mkdir -p tmp
pushd tmp
echo "Info: Exporting source code"
set -x

(cd ${BUILDER_TOP_DIR}; git archive --format=tar --prefix=${KIT_BASENAME}/ master) | tar xf -

mkdir -p ${KIT_BASENAME}/Import/GitPython
(cd ~/wc/git/GitPython; git archive --format=tar --prefix=GitPython/ master) | tar xf - -C ${KIT_BASENAME}/Import
rm -rf ${KIT_BASENAME}/Import/GitPython/git/ext

tar czf ${KIT_BASENAME}.tar.gz ${KIT_BASENAME}
popd

echo "Info: creating ${KITNAME}.spec"
python3 spec_set_version.py ${KITNAME}.spec ${V}

echo "Info: Creating SRPM for ${KIT_BASENAME}"

sudo \
    mock \
        --buildsrpm --dnf \
        --spec ${KITNAME}.spec \
        --sources tmp/${KIT_BASENAME}.tar.gz

MOCK_ROOT=$( sudo mock -p )
MOCK_BUILD_DIR=${MOCK_ROOT}/builddir/build
ls -l ${MOCK_BUILD_DIR}/SRPMS

set $(tr : ' ' </etc/system-release-cpe)
case $4 in
fedora)
    DISTRO=fc$5
    ;;
*)
    echo "Error: need support for distro $4"
    exit 1
    ;;
esac

SRPM_BASENAME="${KIT_BASENAME}-1.${DISTRO}"

cp -v "${MOCK_BUILD_DIR}/SRPMS/${SRPM_BASENAME}.src.rpm" tmp

echo "Info: Creating RPM"
sudo \
    mock \
        --rebuild --dnf \
        --arch=noarch \
            "tmp/${SRPM_BASENAME}.src.rpm"

ls -l ${MOCK_BUILD_DIR}/RPMS

cp -v "${MOCK_BUILD_DIR}/RPMS/${SRPM_BASENAME}.noarch.rpm" tmp

echo "Info: Results in ${PWD}/tmp:"
ls -l tmp

if [ "$CMD" = "--install" ]
then
    echo "Info: Installing RPM"
    sudo dnf -y remove ${KITNAME}
    sudo dnf -y install "tmp/${SRPM_BASENAME}.noarch.rpm"
fi
