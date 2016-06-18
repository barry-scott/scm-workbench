all: wb_diff_images.py

wb_diff_images.py: make_wb_diff_images.py
	python3 make_wb_diff_images.py
