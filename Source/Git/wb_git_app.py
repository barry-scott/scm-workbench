'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_app.py

'''
import wb_app
import wb_platform_specific

import wb_git_main_window
import wb_git_preferences
import wb_git_debug

class WbGitApp(wb_app.WbApp,
               wb_git_debug.WbGitDebug):
    def __init__( self, args ):
        self.__git_debug = False

        wb_git_debug.WbGitDebug.__init__( self )
        wb_app.WbApp.__init__( self, ('Git', 'Workbench'), args )

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
        # turn on GitPython debug is required
        import git
        if self.__git_debug:
            git.Git.GIT_PYTHON_TRACE = 'full'
        else:
            git.Git.GIT_PYTHON_TRACE = False

    def createPreferences( self ):
        return wb_git_preferences.Preferences(
                    self,
                    wb_platform_specific.getPreferencesFilename() )

    def createMainWindow( self ):
        return wb_git_main_window.WbGitMainWindow( self )
