#!/bin/bash
python3 ./package_workbench.py ${1:-copr-testing} \
    --colour \
    --mock-target=epel-8-x86_64
