#!/bin/bash
set -e
${PYTHON} make_po_file.py ${1?locale missing}
