'''

 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_scm_preferences.py

'''
import pathlib
import sys

import wb_preferences

from  xml_preferences import Scheme, SchemeNode, PreferencesNode


Bool = wb_preferences.Bool

class Preferences(wb_preferences.Preferences):
    xml_attribute_info = wb_preferences.Preferences.xml_attribute_info

    def __init__( self ):
        super().__init__()
        self.log_history = None



class LogHistory(PreferencesNode):
    xml_attribute_info = (('default_limit', int)
                         ,('use_default_limit', Bool)
                         ,('default_until_days_interval', int)
                         ,('use_default_until_days_interval', Bool)
                         ,('default_since_days_interval', int)
                         ,('use_default_since_days_interval', Bool))

    def __init__( self ):
        super().__init__()

        self.default_limit = 20
        self.use_default_limit = False
        self.default_until_days_interval = 0
        self.use_default_until_days_interval = False
        self.default_since_days_interval = 7
        self.use_default_since_days_interval = False


preferences_scheme = (
    Scheme(
        (wb_preferences.scheme_nodes
        << SchemeNode( LogHistory, 'log_history' )
        )
    )
)

class PreferencesManager(wb_preferences.PreferencesManager):
    def __init__( self, log, filename ):
        super().__init__( log, filename, preferences_scheme, Preferences )


if __name__ == '__main__':
    class FakeLog:
        def __init__( self ):
            pass

        def info( self, msg ):
            print( 'Info: %s' % (msg,) )

        def error( self, msg ):
            print( 'Error: %s' % (msg,) )

    # only used in development so not using tempfile module
    # as the file names need to be easy to find
    pm = PreferencesManager( FakeLog(), sys.argv[1] )
    pm.readPreferences()

    p = pm.getPreferences()
    p.dumpPreferences()
    pm.writePreferences()
