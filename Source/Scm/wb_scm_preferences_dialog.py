'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_main_window.py

    Based on code from pysvn WorkBench

'''
import sys
import pathlib

import wb_shell_commands

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

class WbGitPreferencesDialog(QtWidgets.QDialog):
    def __init__( self, app, parent ):
        self.app = app

        super().__init__( parent )

        self.editor_page = EditorPage( self.app )
        self.shell_page = ShellPage( self.app )
        self.log_history_page = LogHistoryPage( self.app )

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab( self.editor_page, T_('Editor') )
        self.tabs.addTab( self.shell_page, T_('Shell') )
        self.tabs.addTab( self.log_history_page, T_('Log History') )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.tabs )
        self.layout.addWidget( self.buttons )

        self.setLayout( self.layout )

        self.resize( 600, 500 )

    def savePreferences( self ):
        self.editor_page.savePreferences()
        self.shell_page.savePreferences()
        self.log_history_page.savePreferences()

class EditorPage(QtWidgets.QWidget):
    def __init__( self, app ):
        self.app = app
        if self.app is None:
            self.prefs = None
        else:
            self.prefs = self.app.prefs.editor

        super().__init__()

        self.editor_program = QtWidgets.QLineEdit( '' )
        self.editor_options = QtWidgets.QLineEdit( '' )

        if self.prefs is not None:
            self.editor_program.setText( self.prefs.program )
            self.editor_options.setText( self.prefs.options )

        self.browse = QtWidgets.QPushButton( T_('Browse…') )

        self.layout = QtWidgets.QGridLayout()
        self.layout.setAlignment( QtCore.Qt.AlignTop )
        self.layout.addWidget( QtWidgets.QLabel( T_('Editor') ), 0, 0 )
        self.layout.addWidget( self.editor_program, 0, 1 )
        self.layout.addWidget( self.browse, 0, 2 )
        self.layout.addWidget( QtWidgets.QLabel( T_('Editor Options') ), 1, 0 )
        self.layout.addWidget( self.editor_options, 1, 1 )

        self.setLayout( self.layout )

        self.browse.clicked.connect( self.pickEditor )

    def savePreferences( self ):
        if self.prefs is None:
            return

        self.prefs.program = self.editor_program.text()
        self.prefs.options = self.editor_options.text()

    def pickEditor( self ):
        file_browser = QtWidgets.QFileDialog( self )
        file_browser.setFileMode( file_browser.ExistingFile )
        file_browser.setOption( file_browser.ReadOnly, True )
        file_browser.setOption( file_browser.DontResolveSymlinks, True )
        file_browser.setViewMode( file_browser.Detail )
        # Without Readable will not return a Executable image
        file_browser.setFilter( QtCore.QDir.Files|QtCore.QDir.Executable|QtCore.QDir.Readable )

        path = pathlib.Path( self.editor_program.text() )
        if str(path) != '.':
            file_browser.setDirectory( str( path.parent ) )
            file_browser.selectFile( str( path ) )
        else:
            if sys.platform != 'win32':
                file_browser.setDirectory( '/usr/bin' )

        if file_browser.exec_():
            all_files = file_browser.selectedFiles()
            assert len(all_files) == 1
            self.editor_program.setText( all_files[0] )

class ShellPage(QtWidgets.QWidget):
    def __init__( self, app ):
        self.app = app
        if self.app is None:
            self.prefs = None
        else:
            self.prefs = self.app.prefs.shell

        super().__init__()

        terminal_program_list = wb_shell_commands.getTerminalProgramList()
        file_browser_program_list = wb_shell_commands.getFileBrowserProgramList()

        self.terminal_program = QtWidgets.QComboBox()
        self.terminal_program.addItems( terminal_program_list )
        self.terminal_init = QtWidgets.QLineEdit( '' )
        self.file_browser_program = QtWidgets.QComboBox()
        self.file_browser_program.addItems( file_browser_program_list )

        if self.prefs is not None:
            self.terminal_program.setCurrentText( self.prefs.terminal_program )
            self.terminal_init.setText( self.prefs.terminal_init )
            self.file_browser_program.setCurrentText( self.prefs.file_browser )

        self.layout = QtWidgets.QGridLayout()
        self.layout.setAlignment( QtCore.Qt.AlignTop )
        self.layout.addWidget( QtWidgets.QLabel( T_('Terminal Program') ), 0, 0 )
        self.layout.addWidget( self.terminal_program, 0, 1 )
        self.layout.addWidget( QtWidgets.QLabel( T_('Terminal Init Command') ), 1, 0 )
        self.layout.addWidget( self.terminal_init, 1, 1 )
        self.layout.addWidget( QtWidgets.QLabel( T_('File Browser Program') ), 2, 0 )
        self.layout.addWidget( self.file_browser_program, 2, 1 )

        self.setLayout( self.layout )

    def savePreferences( self ):
        if self.prefs is None:
            return

        self.prefs.terminal_program = self.terminal_program.currentText()
        self.prefs.terminal_init = self.terminal_init.text()
        self.prefs.file_browser = self.file_browser_program.currentText()

class LogHistoryPage(QtWidgets.QWidget):
    def __init__( self, app ):
        self.app = app
        if self.app is None:
            self.prefs = None
        else:
            self.prefs = self.app.prefs.log_history

        super().__init__()

        self.default_limit = QtWidgets.QSpinBox()
        self.default_limit.setRange( 1, 100000 )
        self.default_limit.setSuffix( T_(' Commits') )

        self.use_default_limit = QtWidgets.QCheckBox( T_('Use limit') )

        self.default_until = QtWidgets.QSpinBox()
        self.default_until.setRange( 1, 365 )
        self.default_until.setSuffix( T_(' days') )

        self.use_default_until = QtWidgets.QCheckBox( T_('Use until') )

        self.default_since = QtWidgets.QSpinBox()
        self.default_since.setRange( 2, 365 )
        self.default_since.setSuffix( T_(' days') )

        self.use_default_since = QtWidgets.QCheckBox( T_('Use since') )

        if self.prefs is not None:
            self.default_limit.setValue( self.prefs.default_limit )
            self.use_default_limit.setChecked( self.prefs.use_default_limit )

            self.default_until.setValue( self.prefs.default_until_days_interval )
            self.use_default_until.setChecked( self.prefs.use_default_until_days_interval )

            self.default_since.setValue( self.prefs.default_since_days_interval )
            self.use_default_since.setChecked( self.prefs.use_default_since_days_interval )

        self.layout = QtWidgets.QGridLayout()
        self.layout.setAlignment( QtCore.Qt.AlignTop )
        self.layout.addWidget( QtWidgets.QLabel( T_('Default Limit') ), 0, 0 )
        self.layout.addWidget( self.default_limit, 0, 1 )
        self.layout.addWidget( self.use_default_limit, 0, 2 )

        self.layout.addWidget( QtWidgets.QLabel( T_('Default until interval') ), 1, 0 )
        self.layout.addWidget( self.default_until, 1, 1 )
        self.layout.addWidget( self.use_default_until, 1, 2 )

        self.layout.addWidget( QtWidgets.QLabel( T_('Default since interval') ), 2, 0 )
        self.layout.addWidget( self.default_since, 2, 1 )
        self.layout.addWidget( self.use_default_since, 2, 2 )

        self.setLayout( self.layout )

        self.default_until.valueChanged.connect( self.__untilChanged )

    def __untilChanged( self ):
        v_until = self.default_until.value()
        v_since = self.default_since.value()

        if (v_until+1) > v_since:
            self.default_since.setValue( v_until + 1 )

        self.default_since.setMinimum( v_until + 1 )

    def savePreferences( self ):
        if self.prefs is None:
            return

        self.prefs.default_limit = self.default_limit.value()
        self.prefs.use_default_limit = self.use_default_limit.isChecked()

        self.prefs.default_until_days_interval = self.default_until.value()
        self.prefs.use_default_until_days_interval = self.use_default_until.isChecked()

        self.prefs.default_since_days_interval = self.default_since.value()
        self.prefs.use_default_since_days_interval = self.use_default_since.isChecked()

if __name__ == '__main__':
    def T_(s):
        return s

    app = QtWidgets.QApplication( ['foo'] )

    prefs = WbGitPreferencesDialog( None, None )
    if prefs.exec_():
        print( 'o.k.' )

    else:
        print( 'Cancelled' )

    # force objects to be cleanup to avoid segv on exit
    del app
