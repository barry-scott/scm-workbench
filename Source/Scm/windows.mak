#
#	makefile WorkBench
#
DEL=del
all: locale\en\LC_MESSAGES\scm_workbench.mo wb_scm_images.py

locale\en\LC_MESSAGES\scm_workbench.mo: wb_scm_version.py
	if not exist locale\en\LC_MESSAGES mkdir locale\en\LC_MESSAGES
	make-pot-file.cmd
	make-po-file.cmd en
	make-mo-files.cmd locale

clean::
	if exist locale rmdir /s /q locale
	del I18N\*.current.po

include wb_scm_common.mak
