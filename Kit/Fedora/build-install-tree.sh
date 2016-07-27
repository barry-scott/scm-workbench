#!/usr/bin/bash
set -e

echo "Info: build-install-tree.sh"
BIN=${1? bin folder}
LIB=${2? lib folder}
MAN1=${2? man1 folder}
DESKTOPFILES=${3? desktop files folder}

mkdir -p ${BIN} ${LIB} ${MAN1} ${DESKTOPFILES}

gzip -c ${BUILDER_TOP_DIR}/Kits/Linux/scm-workbench.1 > ${MAN1}/scm-workbench.1.gz
cp ${BUILDER_TOP_DIR}/Kits/Linux/scm-workbench.desktop ${DESKTOPFILES}

cat <<EOF >${BIN}/scm-workbench
#!/usr/bin/python3
import sys
sys.path.insert( 0, "${LIB}" )
EOF

cat ${BUILDER_TOP_DIR}/Source/Scm/wb_scm_main.py >>${BIN}/scm-workbench
chmod +x ${BIN}/scm-workbench

pushd ${BUILDER_TOP_DIR}/Source/Scm
make -f linux.mak
popd

for LIBSRC in \
    ${BUILDER_TOP_DIR}/Source/Common \
    ${BUILDER_TOP_DIR}/Source/Git \
    ${BUILDER_TOP_DIR}/Source/Hg \
    ${BUILDER_TOP_DIR}/Source/Svn \
    ${BUILDER_TOP_DIR}/Source/Scm
do
    cp ${LIBSRC}/*.py ${LIB}
done

# hack until GitPython is packaged by fedora
cp -r ${BUILDER_TOP_DIR}/Import/GitPython/git ${LIB}/git
