#!/bin/bash
REPO=${TMPDIR:? set TMPDIR}/test-repo-status

rm -rf ${TMPDIR:? set TMPDIR}/test-repo-status

mkdir ${REPO}
git init ${REPO}
mkdir ${REPO}/Folder1
mkdir ${REPO}/Folder2

echo deleted-sh-rm.txt >${REPO}/Folder1/deleted-sh-rm.txt
echo deleted-git-rm.txt >${REPO}/Folder1/deleted-git-rm.txt
echo renamed.txt >${REPO}/Folder1/renamed.txt
echo changed-staged.txt >${REPO}/Folder1/changed-staged.txt
echo changed-working.txt >${REPO}/Folder1/changed-working.txt

git add \
    ${REPO}/Folder1/deleted-sh-rm.txt \
    ${REPO}/Folder1/deleted-git-rm.txt \
    ${REPO}/Folder1/renamed.txt \
    ${REPO}/Folder1/changed-staged.txt \
    ${REPO}/Folder1/changed-working.txt \
    ;

git commit -m "commit 1"

rm ${REPO}/Folder1/deleted-sh-rm.txt
git rm ${REPO}/Folder1/deleted-git-rm.txt
git mv ${REPO}/Folder1/renamed.txt ${REPO}/Folder2/renamed2.txt

echo staged change >> ${REPO}/Folder1/changed-staged.txt
git add ${REPO}/Folder1/changed-staged.txt 
echo working chage >> ${REPO}/Folder1/changed-working.txt

rm ${REPO}/Folder1/deleted-sh-rm.txt
git rm ${REPO}/Folder1/deleted-git-rm.txt

echo new-working.txt > ${REPO}/Folder1/new-working.txt
echo new-staged.txt > ${REPO}/Folder1/new-staged.txt
git add ${REPO}/Folder1/new-staged.txt

git status ${REPO}
