'''

 ====================================================================
 Copyright (c) 2003-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_svn_preferences.py

'''
import pathlib
import shutil

from PyQt5 import QtWidgets
from PyQt5 import QtCore

from xml_preferences import XmlPreferences, Scheme, SchemeNode, PreferencesNode, PreferencesMapNode, ParseError

import wb_pick_path_dialogs
import wb_platform_specific
import wb_dialog_bases

def getAllPreferenceTabs( app ):
    return [SvnPreferencesTab( app )]

def setupPreferences( scheme_nodes ):
    pass

class SvnPreferencesTab(wb_dialog_bases.WbTabBase):
    def __init__( self, app ):
        super().__init__( app, T_('Svn') )

        self.addRow( T_('Svn Program'), T_('Using built-in PySvn client') )

    def savePreferences( self ):
        pass
