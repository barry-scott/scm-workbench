#
#	makefile Scm/I18N
#
all: $(LOCALE)

$(LOCALE):
	mkdir -p $(LOCALE)
	PYTHONPATH=.. $(PYTHON) make_pot_file.py
	PYTHONPATH=.. $(PYTHON) make_po_file.py en
	PYTHONPATH=.. $(PYTHON) make_mo_files.py locale

clean::
	rm -f *.current.po
