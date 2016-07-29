all: wb_diff_images.py

wb_diff_images.py: make_wb_diff_images.py
	$(PYTHON) make_wb_diff_images.py

clean::
	rm -f wb_diff_images.py
