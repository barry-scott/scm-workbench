#!/bin/bash
set -x

rm -rf tmp
mkdir tmp

git clone https://github.com/barry-scott/testrepo.git tmp/repo1
git clone https://github.com/barry-scott/testrepo.git tmp/repo2

(cd tmp/repo1; ./push-change.sh)

(cd tmp/repo2; echo A change >World.txt)

export HOME=$PWD/tmp
mkdir $HOME/.ScmWorkbench
cp ScmWorkbench.xml $HOME/.ScmWorkbench/

(cd ../Source/Scm; ./wb-scm.sh)
exit 0

git stash save
git stash list
git pull --rebase
git stash pop
