#
#	makefile WorkBench
#
DEL=del
all: locale\en\LC_MESSAGES\scm_workbench.mo wb_scm_images.py

locale\en\LC_MESSAGES\scm_workbench.mo: wb_scm_version.py
	if not exist locale\en\LC_MESSAGES mkdir locale\en\LC_MESSAGES
	cd I18N & $(PYTHON) make_pot_file.py
	cd I18N & $(PYTHON) make_po_file.py en
	cd I18N & $(PYTHON) make_mo_files.py ..\locale

clean::
	if exist locale rmdir /s /q locale
	echo zzz >I18N\zzzqqqzzz.current.po
	del I18N\*.current.po

include wb_scm_common.mak
