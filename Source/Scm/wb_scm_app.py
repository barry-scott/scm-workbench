'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_app.py

'''
import sys

import wb_app
import wb_platform_specific

import wb_scm_main_window
import wb_scm_preferences
import wb_scm_debug

import wb_git_ui_components
import wb_hg_ui_components
import wb_svn_ui_components

import wb_hg_preferences

from PyQt5 import QtGui

class WbScmApp(wb_app.WbApp,
               wb_scm_debug.WbScmDebug):
    def __init__( self, args ):
        self.__git_debug = False
        self.__all_singletons = {}

        wb_scm_debug.WbScmDebug.__init__( self )
        wb_app.WbApp.__init__( self, ('Scm', 'Workbench'), args, ['git.cmd'] )

    def addSingleton( self, name, value ):
        assert name not in self.__all_singletons
        self.__all_singletons[ name ] = value

    def hasSingleton( self, name ):
        return name in self.__all_singletons

    def getSingleton( self, name ):
        return self.__all_singletons[ name ]

    def popSingleton( self, name ):
        value = self.__all_singletons[ name ]
        del self.__all_singletons[ name ]
        return value

    def getAllSingletons( self ):
        return list( self.__all_singletons.values() )

    def optionParse( self, args ):
        if args[1] == '--git-debug':
            self.__git_debug = True
            del args[ 1 ]
            return True

        return False

    def extraDebugEnabled( self ):
        # tells wb_logging to turn on debug for git.cmd
        return self.__git_debug

    def setupScmDebug( self ):
        # turn on ScmPython debug is required
        import git
        import logging

        if self.__git_debug:
            git.Git.GIT_PYTHON_TRACE = 'full'
            git_log = logging.getLogger( 'git.cmd' )
            git_log.setLevel( logging.DEBUG )

        else:
            git.Git.GIT_PYTHON_TRACE = False

    def createPreferencesManager( self ):
        return wb_scm_preferences.PreferencesManager(
                    self,
                    self.log,
                    wb_platform_specific.getPreferencesFilename(),
                    (wb_hg_preferences.setupPreferences,),
                    (wb_hg_preferences.getAllPreferenceTabs,)
                    )

    def writePreferences( self ):
        super().writePreferences()

        if self.prefs.font.face is not None:
            self.setStyleSheet( '* { font-family: "%s"; font-size: %dpt}' % (self.prefs.font.face, self.prefs.font.point_size) )

    def createMainWindow( self ):
        if self.prefs.font.face is not None:
            self.setStyleSheet( '* { font-family: "%s"; font-size: %dpt}' % (self.prefs.font.face, self.prefs.font.point_size) )

        self.top_window = wb_scm_main_window.WbScmMainWindow( self,
            {'git': wb_git_ui_components.GitMainWindowComponents()
            ,'hg':  wb_hg_ui_components.HgMainWindowComponents()
            ,'svn': wb_svn_ui_components.SvnMainWindowComponents()} )

        return self.top_window
