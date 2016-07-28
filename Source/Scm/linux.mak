#
#	makefile WorkBench
#
DEL=rm
all: locale/en/LC_MESSAGES/scm_workbench.mo all_common

locale/en/LC_MESSAGES/scm_workbench.mo: wb_scm_version.py
	mkdir -p locale/en/LC_MESSAGES
	./make-pot-file.sh
	./make-po-file.sh en
	./make-mo-files.sh locale

clean::
	rm -rf locale
	rm -f I18N/*.current.po

include wb_scm_common.mak
