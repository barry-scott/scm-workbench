'''
 ====================================================================
 Copyright (c) 2018 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_p4_ui_components.py

'''
import P4

import wb_ui_components
import wb_p4_project


class P4MainWindowComponents(wb_ui_components.WbMainWindowComponents):
    def __init__( self, factory ):
        self.all_visible_table_columns = None

        super().__init__( 'p4', factory )

    def setTopWindow( self, top_window ):
        super().setTopWindow( top_window )

    def createProject( self, project ):
        tm = self.table_view.table_model
        self.all_visible_table_columns = (tm.col_status, tm.col_name, tm.col_date)

        project = wb_p4_project.P4Project( self.app, project, self )
        project.cmdConnect()

        return project

    #------------------------------------------------------------
    def addProjectPreInitWizardHandler( self, name, url, wc_path ):
        self.log.infoheader( T_('Initialise P4 repository in %s') % (wc_path,) )
        self.setStatusAction( T_('Init %(project)s') %
                                    {'project': name} )
        self.progress.start( T_('No progress available for p4') )

    # runs on the background thread
    def addProjectInitWizardHandler_Bg( self, wc_path ):
        p4_project = wb_p4_project.P4Project( self.app, None, self )
        try:
            p4_project.cmdInit( wc_path,
                self.deferRunInForeground( self.ui_actions.p4OutputHandler ),
                self.deferRunInForeground( self.ui_actions.p4ErrorHandler ),
                self.ui_actions.p4CredentialsPrompt,
                self.ui_actions.p4AuthFailed )
            return True

        except p4lib.error.ServerError as e:
            self.app.log.error( T_('Failed to init P4 repo %r') % (p4_project.path,) )
            self.app.log.error( T_('p4 error: %s') % (e,) )
            return False

    def addProjectPostInitWizardHandler( self ):
        self.progress.end()
        self.setStatusAction()

    #------------------------------------------------------------
    def addProjectPreCloneWizardHandler( self, name, url, wc_path ):
        self.log.infoheader( T_('Cloning P4 repository %(url)s into %(path)s') %
                                    {'url': url, 'path': wc_path} )
        self.setStatusAction( T_('Clone %(project)s') %
                                    {'project': name} )
        self.progress.start( T_('No progress available for p4') )

    # runs on the background thread
    def addProjectCloneWizardHandler_Bg( self, name, url, wc_path, scm_state ):
        try:
            p4_project = wb_p4_project.P4Project( self.app, None, self )
            p4_project.cmdClone( url, wc_path,
                self.deferRunInForeground( self.ui_actions.p4OutputHandler ),
                self.deferRunInForeground( self.ui_actions.p4ErrorHandler ),
                self.ui_actions.p4CredentialsPrompt,
                self.ui_actions.p4AuthFailed )
            return True

        except p4lib.error.ServerError as e:
            self.app.log.error( T_('Failed to clone P4 repo from %(url)s into %(path)s') %
                                {'url': url
                                ,'path': wc_path} )
            self.app.log.error( 'p4 error: %s' % (e,) )
            return False

    def addProjectPostCloneWizardHandler( self ):
        self.progress.end()
        self.setStatusAction()

    #------------------------------------------------------------
    def about( self ):
        return [wb_p4_project.P4Version()]

    def setupDebug( self ):
        self.debugLog = self.main_window.app.debug_options.debugLogP4Ui

    def setupMenuBar( self, mb, addMenu ):
        act = self.ui_actions

        # ----------------------------------------
        m = mb.addMenu( T_('&P4 Information') )
        self.all_menus.append( m )

        addMenu( m, T_('Diff #head vs. Working'), act.treeTableActionP4DiffHeadVsWorking, act.enablerP4DiffHeadVsWorking, 'toolbar_images/diff.png' )
        m.addSeparator()
        addMenu( m, T_('Annotate'), act.tableActionP4Annotate_Bg, act.enablerTableP4Annotate )
        m.addSeparator()
        addMenu( m, T_('Status'), act.treeActionP4Status_Bg )
        m.addSeparator()
        addMenu( m, T_('Change History…'), act.treeTableActionP4LogHistory_Bg, act.enablerP4LogHistory, 'toolbar_images/history.png' )


        # ----------------------------------------
        m = mb.addMenu( T_('&P4 Actions') )
        self.all_menus.append( m )

        addMenu( m, T_('P4 Edit'), act.tableActionP4Edit_Bg, act.enablerP4FilesEdit, 'toolbar_images/add.png' )
        addMenu( m, T_('Add'), act.tableActionP4Add_Bg, act.enablerP4FilesAdd, 'toolbar_images/add.png' )

        m.addSeparator()
        addMenu( m, T_('Revert'), act.tableActionP4Revert_Bg, act.enablerP4FilesRevert, 'toolbar_images/revert.png' )
        addMenu( m, T_('Delete…'), act.tableActionP4Delete_Bg, act.main_window.table_view.enablerTableFilesExists )

        m.addSeparator()
        addMenu( m, T_('Change…'), act.treeActionP4Change, icon_name='toolbar_images/commit.png' )

        m.addSeparator()
        addMenu( m, T_('P4 Connect'), act.treeActionP4Connect_Bg )
        addMenu( m, T_('P4 Login'), act.treeActionP4Login_Bg )

        if hasattr( act, 'treeActionP4Debug1' ):
            m.addSeparator()
            m = mb.addMenu( T_('&P4 Debug') )
            self.all_menus.append( m )
            addMenu( m, T_('Debug 1'), act.treeActionP4Debug1 )

    def setupToolBarAtLeft( self, addToolBar, addTool ):
        t = addToolBar( T_('p4 logo'), style='font-size: 20pt; width: 40px; color: #cc0000' )
        self.all_toolbars.append( t )

        addTool( t, 'P4', self.main_window.projectActionSettings )

    def setupToolBarAtRight( self, addToolBar, addTool ):
        act = self.ui_actions

        # ----------------------------------------
        t = addToolBar( T_('p4 info') )
        self.all_toolbars.append( t )

        addTool( t, T_('Diff'), act.treeTableActionP4DiffSmart, act.enablerP4DiffSmart, 'toolbar_images/diff.png' )
        addTool( t, T_('Change History'), act.treeTableActionP4LogHistory_Bg, act.enablerP4LogHistory, 'toolbar_images/history.png' )

        # ----------------------------------------
        t = addToolBar( T_('p4 state') )
        self.all_toolbars.append( t )

        addTool( t, T_('Add'), act.tableActionP4Add_Bg, act.enablerP4FilesAdd, 'toolbar_images/add.png' )
        t.addSeparator()
        addTool( t, T_('Revert'), act.tableActionP4Revert_Bg, act.enablerP4FilesRevert, 'toolbar_images/revert.png' )
        t.addSeparator()
        addTool( t, T_('Change'), act.treeActionP4Change, icon_name='toolbar_images/commit.png' )

    def setupTableContextMenu( self, m, addMenu ):
        super().setupTableContextMenu( m, addMenu )

        act = self.ui_actions

        m.addSection( T_('Status') )
        addMenu( m, T_('Diff #head vs. Working'), act.tableActionP4DiffHeadVsWorking, act.enablerP4DiffHeadVsWorking, 'toolbar_images/diff.png' )
        m.addSeparator()
        addMenu( m, T_('Annotate'), act.tableActionP4Annotate_Bg, act.enablerTableP4Annotate )

        m.addSection( T_('Status') )
        addMenu( m, T_('Change History…'), act.treeTableActionP4LogHistory_Bg, act.enablerP4LogHistory, 'toolbar_images/history.png' )

        m.addSection( T_('Actions') )
        addMenu( m, T_('P4 Edit'), act.tableActionP4Edit_Bg, act.enablerP4FilesEdit, 'toolbar_images/add.png' )
        addMenu( m, T_('Add'), act.tableActionP4Add_Bg, act.enablerP4FilesAdd, 'toolbar_images/add.png' )
        m.addSeparator()
        addMenu( m, T_('Revert…'), act.tableActionP4Revert_Bg, act.enablerP4FilesRevert, 'toolbar_images/revert.png' )
        addMenu( m, T_('Delete…'), act.tableActionP4Delete_Bg, act.main_window.table_view.enablerTableFilesExists )

    def setupTreeContextMenu( self, m, addMenu ):
        super().setupTreeContextMenu( m, addMenu )

        act = self.ui_actions

        m.addSection( T_('Diff') )
        addMenu( m, T_('Diff HEAD vs. Working'), act.treeActionP4DiffHeadVsWorking, act.enablerP4DiffHeadVsWorking, 'toolbar_images/diff.png' )
