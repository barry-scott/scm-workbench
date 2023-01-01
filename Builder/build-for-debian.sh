#!/bin/bash
CMD=${1:-debian-test-build}

. /etc/os-release
TARGET=/shared/Downloads/BEmacs/beta/${ID}/${VERSION_CODENAME}

python3 ./package_workbench.py ${CMD} \
    --debian-repos=${TARGET} \
    --colour