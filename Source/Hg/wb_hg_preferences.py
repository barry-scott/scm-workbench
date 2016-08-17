'''

 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_scm_preferences.py

'''
import pathlib

from PyQt5 import QtWidgets
from PyQt5 import QtCore

from xml_preferences import XmlPreferences, Scheme, SchemeNode, PreferencesNode, PreferencesMapNode, ParseError

import wb_pick_path_dialogs

class HgPreferences(PreferencesNode):
    xml_attribute_info = (('program', pathlib.Path),)

    def __init__( self, program=None ):
        super().__init__()

        assert program is None or isinstance( program, str )

        self.program = program

def setupPreferences( scheme_nodes ):
    (scheme_nodes
    <<  SchemeNode( HgPreferences, 'hg', store_as='hg' )
    )

def getAllPreferenceTabs( app ):
    return [HgPreferencesTab( app )]

class HgPreferencesTab(QtWidgets.QWidget):
    def __init__( self, app ):
        self.app = app
        self.prefs = self.app.prefs.hg

        super().__init__()

        self.hg_program = QtWidgets.QLineEdit()
        if self.prefs.program is not None:
            self.hg_program.setText( str(self.prefs.program) )

        self.browse_button = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_button.clicked.connect( self.__pickProgram )

        self.layout = QtWidgets.QGridLayout()
        self.layout.setAlignment( QtCore.Qt.AlignTop )
        self.layout.addWidget( QtWidgets.QLabel( T_('Hg Program') ), 0, 0 )
        self.layout.addWidget( self.hg_program, 0, 1 )
        self.layout.addWidget( self.browse_button, 0, 2 )

        self.setLayout( self.layout )

    def name( self ):
        return T_('Hg')

    def savePreferences( self ):
        path = self.hg_program.text()
        if path == '':
            self.prefs.program = None

        else:
            self.prefs.program = pathlib.Path( self.hg_program.text() )

    def __pickProgram( self ):
        program = wb_pick_path_dialogs.pickExecutable( self, pathlib.Path( self.hg_program.text() ) )
        if program is not None:
            self.hg_program.setText( str(program) )

