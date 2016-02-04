wb_git_version.py: wb_git_version.py.template ../Builder/brand_version.py ../Builder/version.info
	$(PYTHON) -u make_wb_git_version.py

wb_git_images.py: make_wb_git_images.py
	$(PYTHON) -u make_wb_git_images.py

run:
	$(PYTHON) -u wb_git_main.py

clean::
	rm -f wb_git_version.py
	rm -f wb_git_images.py
