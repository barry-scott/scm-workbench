'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_hg_ui_components.py.py

'''
import wb_ui_components
import wb_hg_project

class HgMainWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self ):
        super().__init__()

    def setupDebug( self ):
        self._debug = self.main_window.app._debugHgUi

    def setupMenuBar( self, mb, addMenu ):
        pass

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('hg logo'), style='font-size: 20pt; width: 32px; color: #000099' )
        self.all_toolbars.append( t )

        addTool( t, 'Hg', self.main_window.projectActionSettings )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        pass

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

    def setupTreeContextMenu( self, m, addMenu ):
        super().setupTreeContextMenu( m, addMenu )
