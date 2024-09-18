#!/bin/bash
set -e

function usage() {
    cat <<EOF
$0 copr-release|copr-testing <fedora-version> [<arch>]
EOF
}

cmd=${1:-copr-testing}
rel=${2}
case "$3" in
x86_64|aarch64):
    ARCH=${3}
    ;;

"")
    ARCH=$(arch)
    ;;

*)
    usage
    exit 1
    ;;
esac

if [ "${rel}" = "" ]
then
    python3 ./package_workbench.py ${cmd} \
        --colour

else
    python3 ./package_workbench.py ${cmd} \
        --mock-target=fedora-${rel}-${ARCH} \
        --colour
fi
