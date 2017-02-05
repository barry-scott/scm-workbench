'''

 ====================================================================
 Copyright (c) 2003-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_git_preferences.py

'''
import pathlib
import git

from PyQt5 import QtWidgets
from PyQt5 import QtCore

from xml_preferences import XmlPreferences, Scheme, SchemeNode, PreferencesNode, PreferencesMapNode, ParseError

import wb_pick_path_dialogs
import wb_platform_specific
import wb_dialog_bases

class GitPreferences(PreferencesNode):
    xml_attribute_info = (('program', pathlib.Path),)

    def __init__( self, program=None, new_projects_folder=None ):
        super().__init__()

        assert program is None or isinstance( program, str )
        self.program = program

def setupPreferences( scheme_nodes ):
    (scheme_nodes
    <<  SchemeNode( GitPreferences, 'git', store_as='git' )
    )

def getAllPreferenceTabs( app ):
    return [GitPreferencesTab( app )]

class GitPreferencesTab(wb_dialog_bases.WbTabBase):
    def __init__( self, app ):
        super().__init__( app, T_('Git') )

        self.prefs = self.app.prefs.git

        #------------------------------------------------------------
        self.git_program = QtWidgets.QLineEdit()
        if self.prefs.program is not None:
            self.git_program.setText( str(self.prefs.program) )

        else:
            # show the default
            self.git_program.setText( git.Git.GIT_PYTHON_GIT_EXECUTABLE )

        self.browse_program = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_program.clicked.connect( self.__pickProgram )

        self.addRow( T_('Git Program'), self.git_program, self.browse_program )

    def savePreferences( self ):
        path = self.git_program.text()
        if path == '':
            self.prefs.program = None

        else:
            self.prefs.program = pathlib.Path( self.git_program.text() )

    def __pickProgram( self ):
        program = wb_pick_path_dialogs.pickExecutable( self, pathlib.Path( self.git_program.text() ) )
        if program is not None:
            self.git_program.setText( str(program) )
