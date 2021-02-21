#!/bin/bash
cmd=${1:-copr-testing}
rel=${2}
if [ "${rel}" = "" ]
then
    python3 ./package_workbench.py ${cmd} \
        --colour

else
    python3 ./package_workbench.py ${cmd} \
        --mock-target=fedora-${rel}-$(arch) \
        --colour
fi
