'''

 ====================================================================
 Copyright (c) 2003-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_hg_preferences.py

'''
import pathlib
import hglib

from PyQt5 import QtWidgets

from xml_preferences import SchemeNode, PreferencesNode

import wb_pick_path_dialogs
import wb_dialog_bases

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

class HgPreferencesTab(wb_dialog_bases.WbTabBase):
    def __init__( self, app ):
        super().__init__( app, T_('Hg') )

        self.prefs = self.app.prefs.hg

        #------------------------------------------------------------
        self.hg_program = QtWidgets.QLineEdit()
        if self.prefs.program is not None:
            self.hg_program.setText( str(self.prefs.program) )

        else:
            # show the default
            self.hg_program.setText( hglib.HGPATH )

        self.browse_program = QtWidgets.QPushButton( T_('Browse...') )
        self.browse_program.clicked.connect( self.__pickProgram )

        #------------------------------------------------------------
        self.addRow( T_('Hg Program'), self.hg_program, self.browse_program )

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
