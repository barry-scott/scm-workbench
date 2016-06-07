#!/bin/bash
set -x
set -e

SCRIPT_DIR=${PWD}

REPO=${TMPDIR:? set TMPDIR}/test-hg-repo-status

rm -rf ${TMPDIR:? set TMPDIR}/test-hg-repo-status

mkdir ${REPO}

hg init ${REPO}
cd ${REPO}

hg status

mkdir Folder1
mkdir Folder2

echo 1 deleted-sh-rm.txt >Folder1/deleted-sh-rm.txt
echo 1 deleted-git-rm.txt >Folder1/deleted-git-rm.txt
echo 1 renamed.txt >Folder1/renamed.txt
echo 1 changed-staged.txt >Folder1/changed-staged.txt
echo 1 changed-working.txt >Folder1/changed-working.txt
echo 1 changed-staged-and-working.txt >Folder1/changed-staged-and-working.txt

hg add \
    Folder1/deleted-sh-rm.txt \
    Folder1/deleted-git-rm.txt \
    Folder1/renamed.txt \
    Folder1/changed-staged.txt \
    Folder1/changed-working.txt \
    Folder1/changed-staged-and-working.txt \
    ;

hg commit -m "commit 1"

# delete file
rm Folder1/deleted-sh-rm.txt
hg rm Folder1/deleted-git-rm.txt

# rename file
hg mv Folder1/renamed.txt Folder2/renamed2.txt

# modify files
echo 2 staged change >> Folder1/changed-staged.txt
hg add Folder1/changed-staged.txt 

echo 2 working chage >> Folder1/changed-working.txt

echo 2 staged change >> Folder1/changed-staged-and-working.txt
hg add Folder1/changed-staged-and-working.txt 

echo 3 working change >> Folder1/changed-staged-and-working.txt

# new files
echo 3 new-working.txt > Folder1/new-working.txt

echo 3 new-staged.txt > Folder1/new-staged.txt
hg add Folder1/new-staged.txt

# status
hg status

# allow Source/Git modules to be tested
export PYTHONPATH=${BUILDER_TOP_DIR}/Source/Git

python3 ${SCRIPT_DIR}/hglib_status.py ${REPO} $1
#python3 ${SCRIPT_DIR}/hg_wb_project_status.py ${REPO} $1
