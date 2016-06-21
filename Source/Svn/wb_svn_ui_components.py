'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_ui_components.py.py

'''
import wb_ui_components
import wb_svn_project

class SvnMainWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self ):
        super().__init__()

    def setupDebug( self ):
        self._debug = self.main_window.app._debugSvnUi

    def setupMenuBar( self, mb, addMenu ):
        # ----------------------------------------
        m = mb.addMenu( T_('&Svn Information') )
        self.all_menus.append( m )

        addMenu( m, T_('Diff Base vs. Working'), self.treeTableActionSvnDiffBaseVsWorking, self.enablerSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionSvnDiffHeadVsWorking, self.enablerSvnDiffHeadVsWorking, 'toolbar_images/diff.png' )

        m.addSeparator()
        addMenu( m, T_('Log History'), self.treeTableActionSvnLogHistory, self.enablerSvnLogHistory, 'toolbar_images/history.png' )
        addMenu( m, T_('Status'), self.treeActionSvnStatus )

        # ----------------------------------------
        m = mb.addMenu( T_('&Git Actions') )
        self.all_menus.append( m )

        addMenu( m, T_('Add'), self.tableActionSvnAdd, self.enablerSvnFilesUncontrolled, 'toolbar_images/add.png' )
        addMenu( m, T_('Revert'), self.tableActionSvnRevert, self.enablerSvnFilesRevert, 'toolbar_images/revert.png' )

        m.addSeparator()
        addMenu( m, T_('Delete…'), self.tableActionSvnDelete, self.main_window.enablerFilesExists )

        m.addSeparator()
        addMenu( m, T_('Checkin…'), self.treeActionSvnCheckin, self.enablerSvnCheckin, 'toolbar_images/checkin.png' )

        m.addSeparator()
        addMenu( m, T_('Update…'), self.treeActionSvnUpdate, icon_name='toolbar_images/update.png' )

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('svn logo'), style='font-size: 20pt; width: 32px; color: #000099' )
        self.all_toolbars.append( t )

        addTool( t, 'Svn', self.main_window.projectActionSettings )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        # ----------------------------------------
        t = addToolBar( T_('svn info') )
        self.all_toolbars.append( t )

        addTool( t, T_('Diff'), self.treeTableActionSvnDiffBaseVsWorking, self.enablerSvnDiffBaseVsWorking, 'toolbar_images/diff.png' )
        addTool( t, T_('Log History'), self.treeTableActionSvnLogHistory, self.enablerSvnLogHistory, 'toolbar_images/history.png' )

        # ----------------------------------------
        t = addToolBar( T_('svn state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Add'), self.tableActionSvnAdd, self.enablerSvnFilesUncontrolled, 'toolbar_images/add.png' )
        addTool( t, T_('Revert'), self.tableActionSvnRevert, self.enablerSvnFilesRevert, 'toolbar_images/revert.png' )
        t.addSeparator()
        addTool( t, T_('Checkin'), self.treeActionSvnCheckin, self.enablerSvnCheckin, 'toolbar_images/checkin.png' )
        t.addSeparator()
        addTool( t, T_('Update'), self.treeActionSvnUpdate, icon_name='toolbar_images/update.png' )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

    def setupTreeContextMenu( self, m, addMenu ):
        super().setupTreeContextMenu( m, addMenu )

    #--- Enablers ---------------------------------------------------------
    def enablerSvnDiffBaseVsWorking( self, cache ):
        key = 'enablerSvnDiffBaseVsWorking'
        if key not in cache:
            cache[ key ] = True

        return cache[ key ]

    def enablerSvnDiffHeadVsWorking( self, cache ):
        key = 'enablerSvnDiffHeadVsWorking'
        if key not in cache:
            cache[ key ] = True

        return cache[ key ]

    def enablerSvnLogHistory( self, cache ):
        key = 'enablerSvnLogHistory'
        if key not in cache:
            cache[ key ] = True

        return cache[ key ]

    def enablerSvnFilesUncontrolled( self, cache ):
        key = 'enablerSvnFilesUncontrolled'
        if key not in cache:
            cache[ key ] = True

        return cache[ key ]

    def enablerSvnFilesRevert( self, cache ):
        key = 'enablerSvnFilesRevert'
        if key not in cache:
            cache[ key ] = True

        return cache[ key ]

    def enablerSvnCheckin( self, cache ):
        key = 'enablerSvnCheckin'
        if key not in cache:
            cache[ key ] = True

        return cache[ key ]

    #--- Actions ---------------------------------------------------------
    def treeTableActionSvnDiffBaseVsWorking( self ):
        pass

    def treeTableActionSvnDiffHeadVsWorking( self ):
        pass

    def treeTableActionSvnLogHistory( self ):
        pass

    def tableActionSvnAdd( self ):
        pass

    def tableActionSvnRevert( self ):
        pass

    def tableActionSvnDelete( self ):
        pass

    def treeActionSvnCheckin( self ):
        pass

    def treeActionSvnUpdate( self ):
        pass

    def treeActionSvnStatus( self ):
        pass

    #------------------------------------------------------------

