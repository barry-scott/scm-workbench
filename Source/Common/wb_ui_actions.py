'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_ui_actions.py

'''
import difflib

import wb_diff_unified_view
try:
    # If Qsci is not packaged then this import will fail
    import wb_diff_side_by_side_view
    have_side_by_side = True

except ImportError:
    have_side_by_side = False




class WbMainWindowActions:
    def __init__( self, scm_type, factory ):
        self.scm_type = scm_type
        self.factory = factory

        self.setStatusGeneral = None
        self.setStatusAction = None
        self.progress = None
        self.switchToForeground = None
        self.switchToBackground = None
        self.deferRunInForeground = None

        self.top_window = None
        self.main_window = None
        self.table_view = None
        self.app = None
        self.log = None

        self.debugLog = None

    # ---- called from ui_component ----
    def setTopWindow( self, top_window ):
        self.top_window = top_window

        # short cuts
        self.setStatusGeneral = top_window.setStatusGeneral
        self.setStatusAction =  top_window.setStatusAction

        self.progress =         top_window.progress

    # ---- called from ui_component ----
    def setMainWindow( self, main_window, table_view ):
        assert main_window is not None
        self.main_window = main_window

        self.table_view = table_view

        self.app = self.main_window.app
        self.log = self.app.log

        # shorts cut to main window functions
        self.switchToForeground = self.app.switchToForeground
        self.switchToBackground = self.app.switchToBackground
        self.deferRunInForeground = self.app.deferRunInForeground

        self.setupDebug()

    def setupDebug( self ):
        self.debugLog = self.main_window.app.debug_options.debugLogMainWindow

    def tableSelectedAllFileStates( self ):
        if self.table_view is None:
            return []

        return self.table_view.selectedAllFileStates()

    # ------------------------------------------------------------
    def diffTwoFiles( self, title, old_lines, new_lines, header_left, header_right ):
        if self.app.prefs.view.isDiffSideBySide() and have_side_by_side:
            window = wb_diff_side_by_side_view.DiffSideBySideView(
                        self.app, None,
                        title,
                        old_lines, header_left,
                        new_lines, header_right )
            window.show()

        elif self.app.prefs.view.isDiffUnified():
            all_lines = list( difflib.unified_diff( old_lines, new_lines ) )

            self.showDiffText( title, all_lines )

    def showDiffText( self, title, all_lines ):
        assert type(all_lines) == list

        window = wb_diff_unified_view.WbDiffViewText( self.app, title )
        window.setUnifiedDiffText( all_lines )
        window.show()
