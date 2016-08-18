'''

 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

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

class GitPreferences(PreferencesNode):
    xml_attribute_info = (('program', pathlib.Path),)

    def __init__( self, program=None ):
        super().__init__()

        assert program is None or isinstance( program, str )

        self.program = program

def setupPreferences( scheme_nodes ):
    (scheme_nodes
    <<  SchemeNode( GitPreferences, 'git', store_as='git' )
    )

def getAllPreferenceTabs( app ):
    return [GitPreferencesTab( app )]

class GitPreferencesTab(QtWidgets.QWidget):
    def __init__( self, app ):
        self.app = app
        self.prefs = self.app.prefs.git

        super().__init__()

        self.git_program = QtWidgets.QLineEdit()
        if self.prefs.program is not None:
            self.git_program.setText( str(self.prefs.program) )

        else:
            # show the default
            self.git_program.setText( git.Git.GIT_PYTHON_GIT_EXECUTABLE )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickProgram )

        self.layout = QtWidgets.QGridLayout()
        self.layout.setAlignment( QtCore.Qt.AlignTop )
        self.layout.addWidget( QtWidgets.QLabel( T_('Git Program') ), 0, 0 )
        self.layout.addWidget( self.git_program, 0, 1 )
        self.layout.addWidget( self.browse_button, 0, 2 )

        self.setLayout( self.layout )

    def name( self ):
        return T_('Git')

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

