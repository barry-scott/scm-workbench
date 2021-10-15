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

import wb_app
import wb_date
import wb_platform_specific

import wb_scm_main_window
import wb_scm_preferences
import wb_scm_debug
import wb_scm_images

import wb_scm_factories

from PyQt5 import QtGui
from PyQt5 import QtWidgets

if getattr( typing, 'TYPE_CHECKING', False ):
    #pylint: disable=unused-import
    import datetime

class WbScmApp(wb_app.WbApp):
    def __init__( self, args:List[str] ) -> None:
        self.__all_singletons = {}  # type: dict[str, None]

        all_factories, all_messages = wb_scm_factories.allScmFactories()
        # convert to a dict
        self.all_factories = dict( [(f.scmName(), f) for f in all_factories] )

        extra_loggers = []
        for factory in self.all_factories.values():
            extra_loggers.extend( factory.extraLoggers() )

        super().__init__( ('Scm', 'Workbench'), args, debug_class=wb_scm_debug.WbScmDebug, extra_loggers=extra_loggers,  )

        if wb_platform_specific.isUnix():
            self.setDesktopFileName( '/usr/share/applications/org.barrys-emacs.scm-workbench.desktop' )
            self.log.info( 'desktopFileName %r' % (self.desktopFileName(),) )

            self.setApplicationDisplayName( 'org.barrys-emacs.scm-workbench' )

        for msg in all_messages:
            self.log.info( msg )

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
        for factory in self.all_factories.values():
            if factory.optionParse( args ):
                return True

        return False

    def extraDebugEnabled( self ) -> bool:
        for factory in self.all_factories.values():
            if factory.extraDebugEnabled():
                return True

        return False

    def setupAppDebug( self ) -> None:
        for factory in self.all_factories.values():
            factory.setupAppDebug()

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
        style_sheet_pieces.append( 'QLineEdit[valid=false] {border: 1px solid #cc00cc; border-radius: 3px; padding: 5px}' )

        # set the users UI font
        if self.prefs.font_ui.face is not None:
            style_sheet_pieces.append( '* { font-family: "%s"; font-size: %dpt}' % (self.prefs.font_ui.face, self.prefs.font_ui.point_size) )

        if self.isDarkMode():
            style_sheet_pieces.append( 'QToolTip { color: white; background-color: %s; border: 1px solid #888888; }' % (feedback_bg,) )

        style_sheet = '\n'.join( style_sheet_pieces )
        self.debugLogApp( style_sheet )
        self.setStyleSheet( style_sheet )

    def createMainWindow( self ):
        self.setAppStyles()

        self.top_window = wb_scm_main_window.WbScmMainWindow( self, self.all_factories )

        return self.top_window
