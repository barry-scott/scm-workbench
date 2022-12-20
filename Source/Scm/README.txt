Running SCM Workbench from source.
----------------------------------

SCM Workbench requires the following software to be installed.

You can install using python3 -m pip if the software is not already
packaged for your operating system.

    python
    PyQt6
    pytz
    PyQt6-QScintilla
    tzlocal
    xml-preferences

Use the requirements.txt for your OS to install all dependencies at
versions that are know to work well.

For macOS Kit/macOS/requirements.txt
For Windows Kit/Windows/requirements.txt

For example on Windows:
    py -3.7-64 -m pip install --user --upgrade -r Kit/Windows/requirements.txt

For example on macOS:
    python3.7 -m pip install --user --upgrade -r Kit/macOS/requirements.txt

Note: pysvn is available as a package for most linux systems.
For Windows and macOS get a binary kit from:

    https://pysvn.sourceforge.io/downloads.html

If you wish to work with Git you will also need:

    GitPython>=2.1.1

If you wish to work with Mercurial you will also need:

    python-hglib>=2.3

If you wish to work with Subversion you will also need:

    pysvn>=1.9.2

You will also need the to install command line clients for git and Mercurial.

For Windows:
    https://gitforwindows.org/

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
