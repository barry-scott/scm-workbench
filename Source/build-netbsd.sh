#!/bin/sh
ROOT_DIR=${1:? Root dir}
BIN_DIR=${2:? Bin dir}
LIB_DIR=${3:? Lib dir}
DOC_DIR=${4:? Doc dir}

# xml_preferences is not packaged for NetBSD

mkdir -p ${ROOT_DIR}${LIB_DIR}/xml_preferences
cp ~/.local/lib/python3.7/site-packages/xml_preferences/__init__.py ${ROOT_DIR}${LIB_DIR}/xml_preferences

./build-linux.sh "${@}"
