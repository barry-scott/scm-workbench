#!/bin/bash
set -e
echo "Info: PyQt6 build-linux in $( pwd )"

ROOT_DIR=${1:? Root dir}
BIN_DIR=${2:? Bin dir}
LIB_DIR=${3:? Lib dir}
DOC_DIR=${4:? Doc dir}

${PYTHON} ./make_wb_scm_images.py \
    ${ROOT_DIR}${LIB_DIR}/wb_scm_images.py

make -f linux.mak
cd Common
make -f linux.mak
cd ..

for folder in \
    Common \
    Git \
    Hg \
    Perforce \
    Scm \
    Svn \
    ;
do
    cp ${folder}/wb_*.py ${ROOT_DIR}${LIB_DIR}
done
cp Wallet/kwallet.py ${ROOT_DIR}${LIB_DIR}

# see if xml_preferences has been included is in .local
PY_BASENAME=$(basename ${PYTHON})
if [[ -e ~/.local/lib/${PY_BASENAME}/site-packages/xml_preferences/__init__.py ]]
then
    cp ~/.local/lib/${PY_BASENAME}/site-packages/xml_preferences/__init__.py xml_preferences.py
fi

cd ${ROOT_DIR}${LIB_DIR}
${PYTHON} -m compileall *.py
