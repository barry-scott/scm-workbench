#!/usr/bin/bash
#
#   build-rpms.sh
#
set -e
set -x

CMD="$1"
if [ "$2" != "" ]
then
    VERSION_ID=$2
else
    . /etc/os-release
fi

if [ "$3" != "" ]
then
    ARCH=$3
else
    ARCH=$( uname -m )
fi

echo "Info: Creating source tarball"
rm -rf tmp
mkdir -p tmp

KITNAME=scm-workbench

# create a version file for the build process
${PYTHON} -u ${BUILDER_TOP_DIR}/Source/Scm/make_wb_scm_version.py \
    ${BUILDER_TOP_DIR}/Builder/version.dat \
    tmp/wb_scm_version.py

V=$( PYTHONPATH=tmp ${PYTHON} -c "import wb_scm_version;print( '%d.%d.%d' % (wb_scm_version.major, wb_scm_version.minor, wb_scm_version.patch) )" )

KIT_BASENAME=${KITNAME}-${V}

pushd tmp
echo "Info: Exporting source code"

(cd ${BUILDER_TOP_DIR}; git archive --format=tar --prefix=${KIT_BASENAME}/ master) | tar xf -
# create a version file based on the GIT head commit
${PYTHON} -u ${BUILDER_TOP_DIR}/Source/Scm/make_wb_scm_version.py \
    ${BUILDER_TOP_DIR}/Builder/version.dat \
    ${KIT_BASENAME}/Source/Scm/wb_scm_version.py

# xml-preferences is not packaged by Fedora yet - put in Common
mkdir ${KIT_BASENAME}/Source/Common/xml_preferences
cp \
    ~/.local/lib/python${PYTHON_VERSION}/site-packages/xml_preferences/__init__.py \
        ${KIT_BASENAME}/Source/Common/xml_preferences

cp \
    ~/.local/lib/python${PYTHON_VERSION}/site-packages/P4.py \
    ~/.local/lib/python${PYTHON_VERSION}/site-packages/P4API.cpython-${PYTHON_VERSION/./}m-x86_64-linux-gnu.so \
        ${KIT_BASENAME}/Source/Common

# make the source kit
tar czf ${KIT_BASENAME}.tar.gz ${KIT_BASENAME}
ls -l ${KIT_BASENAME}.tar.gz
popd

if [ "${CMD}" = "--tarball" ]
then
    exit 0
fi

MOCK_VERSION_NAME=fedora-${VERSION_ID}-${ARCH}
MOCK_ROOT=$( sudo mock --root=${MOCK_VERSION_NAME} -p )

if [ ! -e "${MOCK_ROOT}" ]
then
    echo "Info: Init mock for ${MOCK_VERSION_NAME}"
    sudo \
         mock \
            --root=${MOCK_VERSION_NAME} \
            --init
fi

echo "Info: creating ${KITNAME}.spec"
PYTHONPATH=tmp python3 spec_set_version.py ${KITNAME}.spec ${V}

echo "Info: Creating SRPM for ${KIT_BASENAME}"
sudo \
    mock \
        --root=${MOCK_VERSION_NAME} \
        --buildsrpm --dnf \
        --spec ${KITNAME}.spec \
        --sources tmp/${KIT_BASENAME}.tar.gz

MOCK_BUILD_DIR=${MOCK_ROOT}/builddir/build
sudo ls -l ${MOCK_BUILD_DIR}/SRPMS

DISTRO=fc${VERSION_ID}

SRPM_BASENAME="${KIT_BASENAME}-1.${DISTRO}"

sudo cp -v "${MOCK_BUILD_DIR}/SRPMS/${SRPM_BASENAME}.src.rpm" tmp

echo "Info: Creating RPM"
sudo \
    mock \
        --root=${MOCK_VERSION_NAME} \
        --rebuild --dnf \
        --arch=x86_64 \
            "tmp/${SRPM_BASENAME}.src.rpm"

sudo ls -l ${MOCK_BUILD_DIR}/RPMS

sudo cp -v "${MOCK_BUILD_DIR}/RPMS/${SRPM_BASENAME}.x86_64.rpm" tmp

echo "Info: Results:"
ls -l ${PWD}/tmp

if [ "$CMD" = "--install" ]
then
    echo "Info: Installing RPM"
    sudo dnf -v -y remove ${KITNAME}
    sudo dnf -v -y install "tmp/${SRPM_BASENAME}.x86_64.rpm"
fi
