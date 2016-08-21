all_common: wb_scm_images.py wb_scm_version.py

wb_scm_images.py: make_wb_scm_images.py
	$(PYTHON) -u make_wb_scm_images.py

wb_scm_version.py: make_wb_scm_version.py
	$(PYTHON) -u make_wb_scm_version.py $(BUILDER_TOP_DIR)/Builder/version.dat wb_scm_version.py

run:
	$(PYTHON) -u wb_scm_main.py

clean::
	$(DEL) wb_scm_images.py
	$(DEL) wb_scm_version.py
