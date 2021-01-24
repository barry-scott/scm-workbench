#
#	makefile SCM
#
DEL=rm -f
LOCALE_TOP=locale
LOCALE=$(LOCALE_TOP)/en/LC_MESSAGES
all: $(LOCALE)/scm_workbench.mo all_common

$(LOCALE)/scm_workbench.mo: Scm/wb_scm_version.py Scm/I18N/linux.mak
	cd Scm/I18N && $(MAKE) -f linux.mak LOCALE=../$(LOCALE)

clean::
	cd Scm/I18N && $(MAKE) -f linux.mak clean
	$(DEL) -r $(LOCALE_TOP)

include wb_scm_common.mak
