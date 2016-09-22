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
import wb_scm_images

import wb_git_factory
import wb_hg_factory
import wb_svn_factory

import wb_hg_preferences
import wb_git_preferences

from PyQt5 import QtGui

class WbScmApp(wb_app.WbApp,
               wb_scm_debug.WbScmDebug):
    def __init__( self, args ):
        self.__git_debug = False
        self.__all_singletons = {}
        self.__code_font = None

        self.all_factories = dict( [(f.scmName(), f)
                                    for f in [wb_git_factory.WbGitFactory()
                                             ,wb_hg_factory.WbHgFactory()
                                             ,wb_svn_factory.WbSvnFactory()]] )

        wb_scm_debug.WbScmDebug.__init__( self )
        wb_app.WbApp.__init__( self, ('Scm', 'Workbench'), args, ['git.cmd'] )

    def getAppQIcon( self ):
        return self.getQIcon( 'wb.png' )

    def getQIcon( self, icon_name ):
        return wb_scm_images.getQIcon( icon_name )

    def getScmFactory( self, scm_type ):
        return self.all_factories[ scm_type ]

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
                    (wb_hg_preferences.setupPreferences
                    ,wb_git_preferences.setupPreferences),
                    (wb_hg_preferences.getAllPreferenceTabs
                    ,wb_git_preferences.getAllPreferenceTabs)
                    )

    def writePreferences( self ):
        super().writePreferences()

        if self.prefs.font_ui.face is not None:
            self.setStyleSheet( '* { font-family: "%s"; font-size: %dpt}' % (self.prefs.font_ui.face, self.prefs.font_ui.point_size) )

        p = self.prefs.font_code
        if p.face is None or p.point_size is None:
            self.__code_font = self.font()

        else:
            self.__code_font = QtGui.QFont( p.face, p.point_size )


    def createMainWindow( self ):
        if self.prefs.font_ui.face is not None:
            self.setStyleSheet( '* { font-family: "%s"; font-size: %dpt}' % (self.prefs.font_ui.face, self.prefs.font_ui.point_size) )

        p = self.prefs.font_code
        if p.face is None or p.point_size is None:
            self.__code_font = self.font()

        else:
            self.__code_font = QtGui.QFont( p.face, p.point_size )

        self.top_window = wb_scm_main_window.WbScmMainWindow( self, self.all_factories )

        return self.top_window

    def getCodeFont( self ):
        return self.__code_font
