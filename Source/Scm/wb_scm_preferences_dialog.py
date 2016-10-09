'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_preferences_dialog.py

    Based on code from pysvn WorkBench

'''
import pathlib

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_pick_path_dialogs
import wb_shell_commands
import wb_platform_specific

class WbScmPreferencesDialog(QtWidgets.QDialog):
    def __init__( self, app, parent ):
        self.app = app

        super().__init__( parent )

        self.tabs = QtWidgets.QTabWidget()
        for tab_class in (EditorTab, ShellTab, LogHistoryTab, FontTab):
            tab = tab_class( self.app )
            self.tabs.addTab( tab, tab.name() )

        for tab in self.app.prefs_manager.getAllPreferenceTabs():
            self.tabs.addTab( tab, tab.name() )

        self.buttons = QtWidgets.QDialogButtonBox()
        self.buttons.addButton( self.buttons.Ok )
        self.buttons.addButton( self.buttons.Cancel )

        self.buttons.accepted.connect( self.accept )
        self.buttons.rejected.connect( self.reject )

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget( self.tabs )
        self.layout.addWidget( self.buttons )

        self.setLayout( self.layout )

        em = self.app.fontMetrics().width( 'm' )
        ex = self.app.fontMetrics().lineSpacing()
        self.resize( 75*em, 40*ex )

    def savePreferences( self ):
        for index in range( self.tabs.count() ):
            tab = self.tabs.widget( index )
            tab.savePreferences()

class EditorTab(QtWidgets.QWidget):
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

    def name( self ):
        return T_('Editor')

    def savePreferences( self ):
        if self.prefs is None:
            return

        self.prefs.program = self.editor_program.text()
        self.prefs.options = self.editor_options.text()

    def pickEditor( self ):
        editor = wb_pick_path_dialogs.pickExecutable( self, pathlib.Path( self.editor_program.text() ) )
        if editor is not None:
            self.editor_program.setText( str(editor) )

class ShellTab(QtWidgets.QWidget):
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

    def name( self ):
        return T_('Shell')

    def savePreferences( self ):
        if self.prefs is None:
            return

        self.prefs.terminal_program = self.terminal_program.currentText()
        self.prefs.terminal_init = self.terminal_init.text()
        self.prefs.file_browser = self.file_browser_program.currentText()

class LogHistoryTab(QtWidgets.QWidget):
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

    def name( self ):
        return T_('Log History')

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

class FontTab(QtWidgets.QWidget):
    def __init__( self, app ):
        super().__init__()

        self.app = app

        p = self.app.prefs.font_ui

        if p.face is None or p.point_size is None:
            font = self.app.font()
            self.ui_face = font.family()
            self.ui_point_size = font.pointSize()

        else:
            self.ui_face = p.face
            self.ui_point_size = p.point_size

        p =  self.app.prefs.font_code

        if p.face is None or p.point_size is None:
            font = self.app.font()
            self.code_face = font.family()
            self.code_point_size = font.pointSize()

        else:
            self.code_face = p.face
            self.code_point_size = p.point_size

        self.ui_font_text = QtWidgets.QLabel( '%s %dpt ' % (self.ui_face, self.ui_point_size) )
        self.ui_font_text.sizePolicy().setHorizontalPolicy( QtWidgets.QSizePolicy.Fixed )
        self.ui_font_text.setFrameStyle( QtWidgets.QFrame.Panel|QtWidgets.QFrame.Sunken )
        self.ui_font_text.setFont( QtGui.QFont( self.ui_face, self.ui_point_size ) )

        self.ui_font_select_font = QtWidgets.QPushButton( T_(' Select Font... ') )

        self.code_font_text = QtWidgets.QLabel( '%s %dpt ' % (self.code_face, self.code_point_size) )
        self.code_font_text.sizePolicy().setHorizontalPolicy( QtWidgets.QSizePolicy.Fixed )
        self.code_font_text.setFrameStyle( QtWidgets.QFrame.Panel|QtWidgets.QFrame.Sunken )
        self.code_font_text.setFont( QtGui.QFont( self.code_face, self.code_point_size ) )

        self.code_font_select_font = QtWidgets.QPushButton( T_(' Select Font... ') )

        self.grid_sizer = QtWidgets.QGridLayout()

        row = 0
        self.grid_sizer.addWidget( QtWidgets.QLabel( T_('User Interface Font:') ), row, 0 )
        self.grid_sizer.addWidget( self.ui_font_text, row, 1 )
        self.grid_sizer.addWidget( self.ui_font_select_font, row, 2 )

        row += 1
        self.grid_sizer.addWidget( QtWidgets.QLabel( T_('Code Font:') ), row, 0 )
        self.grid_sizer.addWidget( self.code_font_text, row, 1 )
        self.grid_sizer.addWidget( self.code_font_select_font, row, 2 )

        self.grid_sizer.setRowStretch( row+1, row+2 )
        self.grid_sizer.setColumnStretch( 1, 2 )

        self.ui_font_select_font.clicked.connect( self.onSelectFontUserInterface )
        self.code_font_select_font.clicked.connect( self.onSelectFontCode )

        self.setLayout( self.grid_sizer )

    def name( self ):
        return T_('Fonts')

    def savePreferences( self ):
        p =  self.app.prefs.font_ui

        p.face = self.ui_face
        p.point_size = self.ui_point_size

        p =  self.app.prefs.font_code

        p.face = self.code_face
        p.point_size = self.code_point_size

    def validate( self ):
        valid = True

        if not valid:
            wx.MessageBox(
                T_('You must enter a valid something'),
                T_('Warning'),
                wx.OK | wx.ICON_EXCLAMATION,
                self )
            return False

        return True

    def onSelectFontUserInterface( self, *args ):
        font = QtGui.QFont( self.ui_face, self.ui_point_size )
        font, ok = QtWidgets.QFontDialog.getFont( font, self, T_('Choose font') )

        if ok:
            self.ui_face = font.family()
            self.ui_point_size = font.pointSize()

            self.ui_font_text.setText( '%s %dpt ' % (self.ui_face, self.ui_point_size) )
            self.ui_font_text.setFont( font )

    def onSelectFontCode( self, *args ):
        font = QtGui.QFont( self.code_face, self.code_point_size )
        font, ok = QtWidgets.QFontDialog.getFont( font, self, T_('Choose font') )

        if ok:
            self.code_face = font.family()
            self.code_point_size = font.pointSize()

            self.code_font_text.setText( '%s %dpt ' % (self.code_face, self.code_point_size) )
            self.code_font_text.setFont( font )

if __name__ == '__main__':
    def T_(s):
        return s

    app = QtWidgets.QApplication( ['foo'] )

    prefs = WbScmPreferencesDialog( None, None )
    if prefs.exec_():
        print( 'o.k.' )

    else:
        print( 'Cancelled' )

    # force objects to be cleanup to avoid segv on exit
    del app
