all_common: Scm/wb_scm_images.py Scm/wb_scm_version.py

Scm/wb_scm_images.py: make_wb_scm_images.py
	$(PYTHON) -u make_wb_scm_images.py

Scm/wb_scm_version.py: make_wb_scm_version.py
	$(PYTHON) -u make_wb_scm_version.py $(BUILDER_TOP_DIR)/Builder/version.dat Scm/wb_scm_version.py

clean::
	$(DEL) Scm/wb_scm_images.py
	$(DEL) Scm/wb_scm_version.py
