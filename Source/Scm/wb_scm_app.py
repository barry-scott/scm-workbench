'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_app.py

'''
import typing
from typing import List, Union, Any

import sys

import wb_app
import wb_date
import wb_platform_specific

import wb_scm_main_window
import wb_scm_preferences
import wb_scm_debug
import wb_scm_images

import wb_git_factory
import wb_hg_factory
import wb_svn_factory

from PyQt5 import QtGui
from PyQt5 import QtWidgets

if getattr( typing, 'TYPE_CHECKING', False ):
    import datetime

class WbScmApp(wb_app.WbApp):
    def __init__( self, args:List[str] ) -> None:
        self.__git_debug = False
        self.__all_singletons = {}  # type: Dict[str, None]
        self.__code_font = None     # type: QtGui.QFont

        self.all_factories = dict( [(f.scmName(), f)
                                    for f in [wb_git_factory.WbGitFactory()
                                             ,wb_hg_factory.WbHgFactory()
                                             ,wb_svn_factory.WbSvnFactory()]] )

        super().__init__( ('Scm', 'Workbench'), args, debug_class=wb_scm_debug.WbScmDebug, extra_loggers=['git.cmd'],  )

    def formatDatetime( self, datetime_or_timestamp:Union[float, 'datetime.datetime'] ) -> str:
        dt = wb_date.localDatetime( datetime_or_timestamp )

        return dt.strftime( '%Y-%m-%d %H:%M:%S' )

    def getAppQIcon( self ):
        return self.getQIcon( 'wb.png' )

    def getQIcon( self, icon_name:str ):
        return wb_scm_images.getQIcon( icon_name )

    def getScmFactory( self, scm_type:str ):
        return self.all_factories[ scm_type ]

    def addSingleton( self, name:str, value:Any ):
        assert name not in self.__all_singletons
        self.__all_singletons[ name ] = value

    def hasSingleton( self, name:str ) -> bool:
        return name in self.__all_singletons

    def getSingleton( self, name:str ) -> Any:
        return self.__all_singletons[ name ]

    def popSingleton( self, name:str ) -> Any:
        value = self.__all_singletons[ name ]
        del self.__all_singletons[ name ]
        return value

    def getAllSingletons( self ) -> List[Any]:
        return list( self.__all_singletons.values() )

    def optionParse( self, args:List[str] ):
        if args[1] == '--git-debug':
            self.__git_debug = True
            del args[ 1 ]
            return True

        return False

    def extraDebugEnabled( self ) -> bool:
        # tells wb_logging to turn on debug for git.cmd
        return self.__git_debug

    def setupAppDebug( self ) -> None:
        # turn on GitPython debug as required
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
                    [factory.setupPreferences for factory in self.all_factories.values()],
                    [factory.getAllPreferenceTabs for factory in self.all_factories.values()]
                    )

    def writePreferences( self ) -> None:
        super().writePreferences()

        self.setAppStyles()

        p = self.prefs.font_code
        if p.face is None or p.point_size is None:
            self.__code_font = self.font()

        else:
            self.__code_font = QtGui.QFont( p.face, p.point_size )

    # place fix style changes in this list
    app_style_sheet = [] # type: List[str]

    def setAppStyles( self ) -> None:
        style_sheet_pieces = self.app_style_sheet[:]

        # get the feedback background-color that matches a dialog background
        dialog = QtWidgets.QDialog()
        palette = dialog.palette()
        feedback_bg = palette.color( palette.Active, palette.Window ).name()

        style_sheet_pieces.append( 'QPlainTextEdit#feedback {background-color: %s; color: #cc00cc}' % (feedback_bg,) )

        style_sheet_pieces.append( 'QPlainTextEdit:read-only {background-color: %s}' % (feedback_bg,) )
        style_sheet_pieces.append( 'QLineEdit:read-only {background-color: %s}' % (feedback_bg,) )

        # set the users UI font
        if self.prefs.font_ui.face is not None:
            style_sheet_pieces.append( '* { font-family: "%s"; font-size: %dpt}' % (self.prefs.font_ui.face, self.prefs.font_ui.point_size) )

        style_sheet = '\n'.join( style_sheet_pieces )
        self._debugApp( style_sheet )
        self.setStyleSheet( style_sheet )

    def createMainWindow( self ):
        self.setAppStyles()

        p = self.prefs.font_code
        if p.face is None or p.point_size is None:
            self.__code_font = self.font()

        else:
            self.__code_font = QtGui.QFont( p.face, p.point_size )

        self.top_window = wb_scm_main_window.WbScmMainWindow( self, self.all_factories )

        return self.top_window

    def getCodeFont( self ) -> 'QtGui.QFont':
        return self.__code_font
