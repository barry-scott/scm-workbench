#
#	makefile WorkBench
#
all: locale/en/LC_MESSAGES/git_workbench.mo wb_git_version.py wb_git_images.py

locale/en/LC_MESSAGES/git_workbench.mo: wb_git_version.py wb_git_images.py
	./make-pot-file.sh
	./make-po-file.sh en
	./make-mo-files.sh locale

include wb_git_common.mak
