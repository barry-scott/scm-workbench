#!/bin/bash
set -x
set -e

SCRIPT_DIR=${PWD}

REPO=${TMPDIR:? set TMPDIR}/test-git-repo-status

rm -rf ${TMPDIR:? set TMPDIR}/test-git-repo-status

mkdir ${REPO}

git init ${REPO}
cd ${REPO}

git branch
git status

mkdir Folder1
mkdir Folder2

cat <<EOF >.gitignore
*~
EOF

echo 1 deleted-sh-rm.txt >Folder1/deleted-sh-rm.txt
echo 1 deleted-git-rm.txt >Folder1/deleted-git-rm.txt
echo 1 renamed.txt >Folder1/renamed.txt
echo 1 changed-staged.txt >Folder1/changed-staged.txt
echo 1 changed-working.txt >Folder1/changed-working.txt
echo 1 changed-staged-and-working.txt >Folder1/changed-staged-and-working.txt

git add \
    .gitignore \
    Folder1/deleted-sh-rm.txt \
    Folder1/deleted-git-rm.txt \
    Folder1/renamed.txt \
    Folder1/changed-staged.txt \
    Folder1/changed-working.txt \
    Folder1/changed-staged-and-working.txt \
    ;

git commit -m "commit 1"

# delete file
rm Folder1/deleted-sh-rm.txt
git rm Folder1/deleted-git-rm.txt

# rename file
git mv Folder1/renamed.txt Folder2/renamed2.txt

# modify files
cp Folder1/changed-staged.txt Folder1/changed-staged.txt~
echo 2 staged change >> Folder1/changed-staged.txt
git add Folder1/changed-staged.txt 

echo 2 working chage >> Folder1/changed-working.txt

echo 2 staged change >> Folder1/changed-staged-and-working.txt
git add Folder1/changed-staged-and-working.txt 

echo 3 working change >> Folder1/changed-staged-and-working.txt

# new files
echo 3 new-working.txt > Folder1/new-working.txt

echo 3 new-staged.txt > Folder1/new-staged.txt
git add Folder1/new-staged.txt

# status
git status

# allow Source/Git modules to be tested
export PYTHONPATH=${BUILDER_TOP_DIR}/Source/Git

python3 ${SCRIPT_DIR}/git_python_status.py ${REPO} $1
python3 ${SCRIPT_DIR}/git_wb_project_status.py ${REPO} $1
