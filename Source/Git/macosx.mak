#
#	Mac OS X makefile for WorkBench
#
all: wb_git_version.py wb_git_images.py locale/en/LC_MESSAGES/git_workbench.mo

locale/en/LC_MESSAGES/git_workbench.mo:
	./make-pot-file.sh
	./make-po-file.sh en
	./make-mo-files.sh locale

clean::	
	rm -rf locale/*

include wb_git_common.mak
