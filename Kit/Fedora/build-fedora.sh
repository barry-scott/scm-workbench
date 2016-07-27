#!/usr/bin/bash
set -e

./build-check-dependancies.sh
./build-install-tree.sh
./build-rpms.sh
