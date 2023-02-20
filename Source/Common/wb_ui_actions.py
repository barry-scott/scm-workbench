'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_ui_actions.py

'''
import subprocess
import difflib
from pathlib import Path
import wb_shell_commands
import wb_platform_specific

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

        if self.app.prefs.view.isDiffSideBySide() and not have_side_by_side:
            self.app.prefs.view.setDiffUnified()

        if self.app.prefs.view.isDiffMeld() and not wb_shell_commands.hasMeld( self.app ):
            self.app.prefs.view.setDiffUnified()

    def setupDebug( self ):
        self.debugLog = self.main_window.app.debug_options.debugLogMainWindow

    def tableSelectedAllFileStates( self ):
        if self.table_view is None:
            return []

        return self.table_view.selectedAllFileStates()

    # ------------------------------------------------------------
    def diffTwoFiles( self, title, old_lines, new_lines, header_left, header_right ):
        if self.app.prefs.view.isDiffMeld() and wb_shell_commands.hasMeld( self.app ):
            self.diffMeldTwoFiles( old_lines, header_left, new_lines, header_right )

        elif self.app.prefs.view.isDiffSideBySide():
            window = wb_diff_side_by_side_view.DiffSideBySideView(
                        self.app, None,
                        title,
                        old_lines, header_left,
                        new_lines, header_right )
            window.show()

        elif self.app.prefs.view.isDiffUnified():
            all_lines = list( difflib.unified_diff( old_lines, new_lines ) )

            self.showDiffText( title, all_lines )

    def diffMeldFolder( self, filename ):
        # call meld with one arg and let it do its magic
        wb_shell_commands.diffMeldFolder(
            self.app, wb_platform_specific.getHomeFolder(),
            filename )

    def diffMeldTwoFiles( self, filename1, header1, filename2, header2 ):
        # call meld with one arg and let it do its magic
        wb_shell_commands.diffMeldTwoFiles(
            self.app, wb_platform_specific.getHomeFolder(),
            filename1, header1,
            filename2, header2 )

    def showDiffText( self, title, all_lines ):
        assert type(all_lines) == list

        window = wb_diff_unified_view.WbDiffViewText( self.app, title )
        window.setUnifiedDiffText( all_lines )
        window.show()
