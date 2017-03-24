Running SCM Workbench from source.
----------------------------------

SCM Workbench requires the following software to be installed.

You can install using python3 -m pip if the software is not already
packaged for your operating system.

    python>=3.5
    PyQt5>=5.7
    pytz>=2016.7
    QScintilla>=2.9.3
    tzlocal>=1.2.2
    xml-preferences>=1.1.2

Note: pysvn is available as a package for most linux systems.
For Windows and macOS get a binary kit from:

    http://pysvn.tigris.org/project_downloads.html

If you wish to work with Git you will also need:

    GitPython>=2.1.1

If you wish to work with Mercurial you will also need:

    python-hglib>=2.3

If you wish to work with Subversion you will also need:

    pysvn>=1.9.2

Having installed the dependencies use the wb-scm.sh script to
run SCM workbench on macOS and Linux systems. Use wb-scm.cmd on
Windows systems.

Command line options
--------------------

SCM Workbench understands a number of command line options that are
useful when developing and debugging.

--noredirect
    Do not redirect stdout and stderr into the SCM Workbench log file.

--log-stdout
    All logs are printed in the terminal window.

--debug <section>
    Turn on debug level logging for the <section>.
    See Common/wb_debug.py and Scm/wb_scm_debug for the
    section names. For example to enable sections 'GIT PROJECT'
    and 'LOG HISTORY'

        --debug git-project,log-history

--git-debug
    Turn on debugging inside of the Git and GitPython.

Example Linux and macOS:
    $ cd Source/Scm
    $ ./wb-scm.sh --noredirect

Example Windows:
    C:\...\Source\Scm> wb-scm.cmd --noredirect
