wb_scm_images.py: make_wb_scm_images.py
	$(PYTHON) -u make_wb_scm_images.py

run:
	$(PYTHON) -u wb_scm_main.py

clean::
	rm -f wb_scm_images.py
