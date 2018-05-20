'''

 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_p4_preferences.py

'''
import wb_dialog_bases

def getAllPreferenceTabs( app ):
    return [P4PreferencesTab( app )]

def setupPreferences( scheme_nodes ):
    pass

class P4PreferencesTab(wb_dialog_bases.WbTabBase):
    def __init__( self, app ):
        super().__init__( app, T_('P4') )

        self.addRow( T_('P4 Program'), T_('Using built-in p4python client') )

    def savePreferences( self ):
        pass
