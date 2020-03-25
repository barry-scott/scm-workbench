'''

 ====================================================================
 Copyright (c) 2003-2017 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================


    wb_scm_preferences.py

'''
import sys
import pathlib

import wb_preferences

from  xml_preferences import Scheme, SchemeNode, PreferencesNode

Bool = wb_preferences.Bool

class Preferences(wb_preferences.Preferences):
    xml_attribute_info = wb_preferences.Preferences.xml_attribute_info

    def __init__( self ):
        super().__init__()
        self.log_history = None

class General(PreferencesNode):
    xml_attribute_info = (('new_projects_folder', pathlib.Path), ('force_dark_mode', Bool))

    def __init__( self ):
        super().__init__()

        self.new_projects_folder = None
        self.force_dark_mode = False

class LogHistory(PreferencesNode):
    xml_attribute_info = (('default_limit', int)
                         ,('use_default_limit', Bool)
                         ,('use_default_since_tag', Bool)
                         ,('default_until_days_interval', int)
                         ,('use_default_until_days_interval', Bool)
                         ,('default_since_days_interval', int)
                         ,('use_default_since_days_interval', Bool))

    def __init__( self ):
        super().__init__()

        self.default_limit = 20
        self.use_default_limit = False
        self.use_default_since_tag = False
        self.default_until_days_interval = 0
        self.use_default_until_days_interval = False
        self.default_since_days_interval = 7
        self.use_default_since_days_interval = False


class PreferencesManager(wb_preferences.PreferencesManager):
    def __init__( self, app, log, filename, all_setup_preferences, all_get_all_preference_tabs ):
        self.app = app

        scheme_nodes = wb_preferences.scheme_nodes
        scheme_nodes << SchemeNode( LogHistory, 'log_history' )
        # general was called project in the past
        scheme_nodes << SchemeNode( General, 'projects_defaults' )

        for setup_preferences in all_setup_preferences:
            setup_preferences( scheme_nodes )

        super().__init__( log, filename, Scheme( scheme_nodes ), Preferences )

        self.all_get_all_preference_tabs = all_get_all_preference_tabs

    def getAllPreferenceTabs( self ):
        all_tabs = []
        for get_all_preference_tabs in self.all_get_all_preference_tabs:
            all_tabs.extend( get_all_preference_tabs( self.app ) )
        return sorted( all_tabs )

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
