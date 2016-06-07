'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_app.py

    Based on code from hg WorkBench

'''
import wb_app
import wb_platform_specific

import wb_hg_main_window
import wb_hg_preferences
import wb_hg_exceptions
import wb_hg_debug

class WbHgApp(wb_app.WbApp,
               wb_hg_debug.WbHgDebug):
    def __init__( self, args ):
        wb_hg_debug.WbHgDebug.__init__( self )
        wb_app.WbApp.__init__( self, ('Hg', 'Workbench'), args )

    def createPreferences( self ):
        return wb_hg_preferences.Preferences(
                    self,
                    wb_platform_specific.getPreferencesFilename() )

    def createMainWindow( self ):
        return wb_hg_main_window.WbHgMainWindow( self )
