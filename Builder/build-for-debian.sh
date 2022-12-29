#!/bin/bash
release=$(( $(<debian_release.txt) + 1 ))
echo $release >debian_release.txt

python3 ./package_workbench.py debian-source \
    --release=${release} \
    --colour
