#
#	makefile WorkBench
#
all: locale/en/LC_MESSAGES/git_workbench.mo wb_git_images.py

locale/en/LC_MESSAGES/git_workbench.mo: wb_git_version.py wb_git_images.py
	mkdir -p locale/en/LC_MESSAGES
	./make-pot-file.sh
	./make-po-file.sh en
	./make-mo-files.sh locale

clean::
	rm -rf locale
	rm -f I18N/*.current.po

include wb_git_common.mak
