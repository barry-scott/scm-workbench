#
#	makefile WorkBench
#
all: locale/en/LC_MESSAGES/hg_workbench.mo wb_hg_images.py

locale/en/LC_MESSAGES/hg_workbench.mo: wb_hg_version.py wb_hg_images.py
	mkdir -p locale/en/LC_MESSAGES
	./make-pot-file.sh
	./make-po-file.sh en
	./make-mo-files.sh locale

clean::
	rm -rf locale
	rm -f I18N/*.current.po

include wb_hg_common.mak
