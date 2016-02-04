#
#	linux-rpmbuild.mak
#
#	make file that is rpmbuild friendly
#
#	Use File locations as preferred by Fedora
#
all:
	cd Source && PYTHON=$(PYTHON) make -f linux.mak

install:
	install --directory $(DESTDIR)/usr/share/git-workbench
	install --mode=644 Source/wb_*.py $(DESTDIR)/usr/share/git-workbench
	rm -f $(DESTDIR)/usr/share/git-workbench/wb_main.py
	install --mode=755 Source/wb_main.py $(DESTDIR)/usr/share/git-workbench
	install --mode=644 Source/wb.png $(DESTDIR)/usr/share/git-workbench
	install --directory $(DESTDIR)/usr/share/doc/git-workbench/WorkBench_files
	install --directory $(DESTDIR)/usr/bin
	ln -s /usr/share/git-workbench/wb_main.py $(DESTDIR)/usr/bin/git-workbench
	install --directory $(DESTDIR)/usr/share/applications
	install --mode=644 Kit/Linux/git-workbench.desktop $(DESTDIR)/usr/share/applications
	gzip Kit/Linux/git-workbench.1
	install --directory $(DESTDIR)/usr/share/man/man1
	install --mode=644 Kit/Linux/git-workbench.1.gz $(DESTDIR)/usr/share/man/man1

install-docs:
	echo "Info: install-docs"
	install --mode=644 Docs/WorkBench.html $(DESTDIR)/usr/share/doc/git-workbench
	install --mode=644 Docs/WorkBench_files/*.png $(DESTDIR)/usr/share/doc/git-workbench/WorkBench_files
