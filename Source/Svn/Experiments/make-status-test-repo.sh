#!/bin/bash
set -x
set -e

SCRIPT_DIR=${PWD}

BASE=${TMPDIR:? set TMPDIR}/test-svn-repo-status
rm -rf ${TMPDIR:? set TMPDIR}/test-svn-repo-status

REPO=${BASE}/repo
WC=${BASE}/wc

mkdir -p ${REPO}

svnadmin create ${REPO}

svn mkdir file://${REPO}/trunk -m "create trunk"

svn checkout file://${REPO}/trunk ${WC}

cd ${WC}

svn status

mkdir Folder1
mkdir Folder1/Folder1.1
mkdir Folder2

echo 1 deleted-sh-rm.txt >Folder1/deleted-sh-rm.txt
echo 1 deleted-svn-rm.txt >Folder1/deleted-svn-rm.txt
echo 1 renamed.txt >Folder1/renamed.txt
echo 1 changed-props.txt >Folder1/changed-props.txt
echo 1 changed-text.txt >Folder1/Folder1.1/changed-text.txt
echo 1 changed-props-and-text.txt >Folder1/changed-props-and-text.txt


svn add Folder1 Folder2
svn commit -m "commit 1"

# delete file
rm Folder1/deleted-sh-rm.txt
svn rm Folder1/deleted-svn-rm.txt

# rename file
svn mv Folder1/renamed.txt Folder2/renamed2.txt

# modify files
svn propset svn:eol-style LF Folder1/changed-props.txt

cp Folder1/Folder1.1/changed-text.txt Folder1/Folder1.1/changed-text.txt~
echo 2 text chage >> Folder1/Folder1.1/changed-text.txt

echo 2 text change >> Folder1/changed-props-and-text.txt

echo 3 text change >> Folder1/changed-props-and-text.txt
svn propset svn:eol-style LF Folder1/changed-props-and-text.txt

# new files
echo 3 new-working.txt > Folder1/new-working.txt

echo 3 new-staged.txt > Folder1/new-staged.txt

# status
svn status
