#!/bin/bash
set -x
set -e

SCRIPT_DIR=${PWD}

REPO=${TMPDIR:? set TMPDIR}/test-repo-status

rm -rf ${TMPDIR:? set TMPDIR}/test-repo-status

mkdir ${REPO}

git init ${REPO}
cd ${REPO}

git branch
git status

mkdir Folder1
mkdir Folder2

echo deleted-sh-rm.txt >Folder1/deleted-sh-rm.txt
echo deleted-git-rm.txt >Folder1/deleted-git-rm.txt
echo renamed.txt >Folder1/renamed.txt
echo changed-staged.txt >Folder1/changed-staged.txt
echo changed-working.txt >Folder1/changed-working.txt

git add \
    Folder1/deleted-sh-rm.txt \
    Folder1/deleted-git-rm.txt \
    Folder1/renamed.txt \
    Folder1/changed-staged.txt \
    Folder1/changed-working.txt \
    ;

git commit -m "commit 1"

# delete file
rm Folder1/deleted-sh-rm.txt
git rm Folder1/deleted-git-rm.txt

# rename file
git mv Folder1/renamed.txt Folder2/renamed2.txt

# modify files
echo staged change >> Folder1/changed-staged.txt
git add Folder1/changed-staged.txt 
echo working chage >> Folder1/changed-working.txt

# new files
echo new-working.txt > Folder1/new-working.txt
echo new-staged.txt > Folder1/new-staged.txt
git add Folder1/new-staged.txt

# status
git status

python3 ${SCRIPT_DIR}/git_python_status.py ${REPO} $1
python3 ${SCRIPT_DIR}/git_wb_project_status.py ${REPO} $1
