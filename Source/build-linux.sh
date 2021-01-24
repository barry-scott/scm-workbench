#!/bin/bash
echo "Info: PyQtBEmacs build-linux in $( pwd )"

ROOT_DIR=${1:? Root dir}
BIN_DIR=${2:? Bin dir}
LIB_DIR=${3:? Lib dir}
DOC_DIR=${4:? Doc dir}

${PYTHON} make_be_images.py

cp be_*.py ${ROOT_DIR}${LIB_DIR}

# see if xml_preferences has been included in the src.rpm
if [[ -e xml_preferences ]]
then
    # its possible to convert into a single file
    cp xml_preferences/__init__.py ${ROOT_DIR}${LIB_DIR}/xml_preferences.py
fi

rm ${ROOT_DIR}${LIB_DIR}/be_client.py

cat <<EOF >${ROOT_DIR}${BIN_DIR}/bemacs_server
#!${PYTHON}
import sys
sys.path.insert( 0, "${LIB_DIR}" )
import be_main
sys.exit( be_main.main( sys.argv ) )
EOF
chmod +x ${ROOT_DIR}${BIN_DIR}/bemacs_server

cat <<EOF >>${ROOT_DIR}${LIB_DIR}/be_platform_unix_specific.py
library_dir = "${LIB_DIR}"
doc_dir = "${DOC_DIR}"
EOF

${PYTHON} create_bemacs_client.py . "${ROOT_DIR}${BIN_DIR}/bemacs"

cd ${ROOT_DIR}${LIB_DIR}
${PYTHON} -m compileall be_*.py
if [[ -e xml_preferences.py ]]
then
    ${PYTHON} -m compileall xml_preferences.py
fi
