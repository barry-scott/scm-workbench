wb_hg_images.py: make_wb_hg_images.py
	$(PYTHON) -u make_wb_hg_images.py

run:
	$(PYTHON) -u wb_hg_main.py

clean::
	rm -f wb_hg_images.py
