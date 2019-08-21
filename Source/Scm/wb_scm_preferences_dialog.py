'''
 ====================================================================
 Copyright (c) 2003-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_preferences_dialog.py

    Based on code from pysvn WorkBench

'''
import pathlib

from PyQt5 import QtWidgets
from PyQt5 import QtGui

import wb_pick_path_dialogs
import wb_shell_commands
import wb_platform_specific
import wb_dialog_bases

class WbScmPreferencesDialog(wb_dialog_bases.WbTabbedDialog):
    def __init__( self, app, parent ):
        self.app = app

        super().__init__( parent=parent, size=(75, 20) )

        self.setWindowTitle( T_('Preferences - %s') % (' '.join( app.app_name_parts ),) )

    def completeTabsInit( self ):
        self.tabs = QtWidgets.QTabWidget()
        for tab_class in (GeneralTab, EditorTab, ShellTab, LogHistoryTab, FontTab):
            tab = tab_class( self.app )
            self.addTab( tab )

        for tab in self.app.prefs_manager.getAllPreferenceTabs():
            self.addTab( tab )

    def savePreferences( self ):
        for index in range( self.tabs.count() ):
            tab = self.tabs.widget( index )
            tab.savePreferences()

class GeneralTab(wb_dialog_bases.WbTabBase):
    def __init__( self, app ):
        super().__init__( app, T_('General') )

        if self.app is None:
            self.prefs = None
        else:
            self.prefs = self.app.prefs.projects_defaults

        self.new_projects_folder = QtWidgets.QLineEdit()
        if self.prefs.new_projects_folder is not None:
            self.new_projects_folder.setText( str(self.prefs.new_projects_folder) )

        else:            # show the default
            self.new_projects_folder.setText( str(wb_platform_specific.getHomeFolder()) )

        self.browse_folder = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_folder.clicked.connect( self.__pickFolder )

        self.addRow( T_('New projects folder'), self.new_projects_folder, self.browse_folder )

        self.dark_theme = QtWidgets.QCheckBox( T_("Force use of a Dark Mode Theme") )
        self.dark_theme.setChecked( self.prefs.force_dark_mode )
        self.addRow( T_('Theme'), self.dark_theme )

    def savePreferences( self ):
        if self.prefs is None:
            return

        self.prefs.new_projects_folder = self.new_projects_folder.text()
        old_dark_mode = self.prefs.force_dark_mode
        self.prefs.force_dark_mode = self.dark_theme.isChecked()

        if old_dark_mode != self.prefs.force_dark_mode:
            QtWidgets.QMessageBox.warning(
                self.app.main_window,
                T_('Restart SCM-Workbench'),
                T_('SCM-Workbench must be restarted too apply the Theme change.') )

    def __pickFolder( self ):
        folder = wb_pick_path_dialogs.pickFolder( self, pathlib.Path( self.new_projects_folder.text() ) )
        if folder is not None:
            self.new_projects_folder.setText( str(folder) )

class EditorTab(wb_dialog_bases.WbTabBase):
    def __init__( self, app ):
        super().__init__( app, T_('Editor') )

        if self.app is None:
            self.prefs = None
        else:
            self.prefs = self.app.prefs.editor

        self.editor_program = QtWidgets.QLineEdit( '' )
        self.editor_options = QtWidgets.QLineEdit( '' )

        if self.prefs is not None:
            self.editor_program.setText( self.prefs.program )
            self.editor_options.setText( self.prefs.options )

        self.browse = QtWidgets.QPushButton( T_('Browse…') )

        self.addRow( T_('Editor'), self.editor_program, self.browse )
        self.addRow( T_('Editor Options'), self.editor_options )

        self.browse.clicked.connect( self.pickEditor )

    def savePreferences( self ):
        if self.prefs is None:
            return

        self.prefs.program = self.editor_program.text()
        self.prefs.options = self.editor_options.text()

    def pickEditor( self ):
        editor = wb_pick_path_dialogs.pickExecutable( self, pathlib.Path( self.editor_program.text() ) )
        if editor is not None:
            self.editor_program.setText( str(editor) )

class ShellTab(wb_dialog_bases.WbTabBase):
    def __init__( self, app ):
        super().__init__( app, T_('Shell') )

        if self.app is None:
            self.prefs = None
        else:
            self.prefs = self.app.prefs.shell

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

        self.addRow( T_('Terminal Program'), self.terminal_program )
        self.addRow( T_('Terminal Init Command'), self.terminal_init )
        self.addRow( T_('File Browser Program'), self.file_browser_program )

    def savePreferences( self ):
        if self.prefs is None:
            return

        self.prefs.terminal_program = self.terminal_program.currentText()
        self.prefs.terminal_init = self.terminal_init.text()
        self.prefs.file_browser = self.file_browser_program.currentText()

class LogHistoryTab(wb_dialog_bases.WbTabBase):
    def __init__( self, app ):
        super().__init__( app, T_('Commit Log History') )

        if self.app is None:
            self.prefs = None
        else:
            self.prefs = self.app.prefs.log_history

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

        self.addRow( T_('Default Limit'), self.default_limit, self.use_default_limit )
        self.addRow( T_('Default until interval'), self.default_until, self.use_default_until )
        self.addRow( T_('Default since interval'), self.default_since, self.use_default_since )

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

class FontTab(wb_dialog_bases.WbTabBase):
    def __init__( self, app ):
        super().__init__( app, 'Fonts' )

        p = self.app.prefs.font_ui

        if p.face is None or p.point_size is None:
            font = self.app.font()
            self.ui_face = font.family()
            self.ui_point_size = font.pointSize()

        else:
            self.ui_face = p.face
            self.ui_point_size = p.point_size

        font = self.app.codeFont()
        self.code_face = font.family()
        self.code_point_size = font.pointSize()

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

        self.addRow( T_('User Interface Font:'), self.ui_font_text, self.ui_font_select_font )
        self.addRow( T_('Code Font:'), self.code_font_text, self.code_font_select_font )

        self.ui_font_select_font.clicked.connect( self.onSelectFontUserInterface )
        self.code_font_select_font.clicked.connect( self.onSelectFontCode )

    def savePreferences( self ):
        p =  self.app.prefs.font_ui

        p.face = self.ui_face
        p.point_size = self.ui_point_size

        p =  self.app.prefs.font_code

        p.face = self.code_face
        p.point_size = self.code_point_size

        # cause the new value to be used
        self.app.code_font = None

    def validate( self ):
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
