#!/bin/bash
cd ${BUILDER_TOP_DIR?run builder_init}/Kits/Fedora/BUILDROOT

tar czf ${TMPDIR:-/tmp}/scm-workbench-tmp.tar.gz usr
sudo tar xzf ${TMPDIR:-/tmp}/scm-workbench-tmp.tar.gz -C /
