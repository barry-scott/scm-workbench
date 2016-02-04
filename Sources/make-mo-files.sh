#!/bin/bash
set -e
${PYTHON} make_mo_files.py ${1:?missing arg 1 output locale dir}
