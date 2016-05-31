'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_git_main_window.py

    Based on code from pysvn WorkBench

'''
import sys
import os
import time
import pathlib
import difflib

# On OS X the packager missing this import
import sip

ellipsis = '…'

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_git_version
import wb_git_images
import wb_git_preferences
import wb_git_preferences_dialog
import wb_git_commit_dialog
import wb_git_config

import wb_git_tree_model
import wb_git_table_model
import wb_git_project
import wb_git_log_history
import wb_git_project_dialogs
import wb_git_status_view

import wb_shell_commands
import wb_logging
import wb_diff_unified_view
import wb_window_chrome_setup

class WbGitMainWindow(QtWidgets.QMainWindow
                     ,wb_window_chrome_setup.WbWindowChromeSetup):
    def __init__( self, app ):
        self.app = app
        self.log = self.app.log
        self._debug = app._debugMainWindow

        # need to fix up how this gets translated
        title = T_( ' '.join( self.app.app_name_parts ) )

        win_prefs = self.app.prefs.getWindow()

        # Why oh Why does python report this:
        # TypeError: __init__() missing 1 required positional argument: 'image_store'
        # image_store is a arg of WbWindowChromeSetup
        QtWidgets.QMainWindow.__init__( self, image_store=None )
        wb_window_chrome_setup.WbWindowChromeSetup.__init__( self, image_store=wb_git_images )

        self.setWindowTitle( title )
        self.setWindowIcon( wb_git_images.getQIcon( 'wb.png' ) )

        # setup the chrome
        self.setupMenuBar( self.menuBar() )
        self.setupToolBar()
        self.setupStatusBar( self.statusBar() )

        self.__setupTreeContextMenu()
        self.__setupTableContextMenu()

        geometry = win_prefs.getFrameGeometry()
        if geometry is not None:
            geometry = QtCore.QByteArray( geometry.encode('utf-8') )
            self.restoreGeometry( QtCore.QByteArray.fromHex( geometry ) )

        else:
            self.resize( 800, 600 )

        # the singleton commit dialog
        self.commit_dialog = None

        self.table_keys_edit = ['\r', 'e', 'E']
        self.table_keys_open = ['o', 'O']

        self.all_table_keys = []
        self.all_table_keys.extend( self.table_keys_edit )
        self.all_table_keys.extend( self.table_keys_open )

        # window major widgets
        self.__log = wb_logging.WbLog( self.app )

        # models and views
        self.__setupTableViewAndModel()
        self.__setupTreeViewAndModel()

        self.filter_text = QtWidgets.QLineEdit()
        self.filter_text.setClearButtonEnabled( True )
        self.filter_text.setMaxLength( 256 )
        self.filter_text.setPlaceholderText( T_('Filter  by name') )

        self.filter_text.textChanged.connect( self.table_sortfilter.setFilterText )

        self.branch_text = QtWidgets.QLineEdit()
        self.branch_text.setReadOnly( True )

        self.folder_text = QtWidgets.QLineEdit()
        self.folder_text.setReadOnly( True )

        # layout widgets in window
        self.v_split = QtWidgets.QSplitter()
        self.v_split.setOrientation( QtCore.Qt.Vertical )

        self.setCentralWidget( self.v_split )

        self.h_split = QtWidgets.QSplitter( self.v_split )
        self.h_split.setOrientation( QtCore.Qt.Horizontal )

        self.v_split_table = QtWidgets.QSplitter()
        self.v_split_table.setOrientation( QtCore.Qt.Vertical )

        self.h_filter_widget = QtWidgets.QWidget( self.v_split )
        self.h_filter_layout = QtWidgets.QGridLayout()

        row = 0
        self.h_filter_layout.addWidget( QtWidgets.QLabel( T_('Filter:') ), row, 0 )
        self.h_filter_layout.addWidget( self.filter_text, row, 1, 1, 3 )

        row += 1
        self.h_filter_layout.addWidget( QtWidgets.QLabel( T_('Branch:') ), row, 0 )
        self.h_filter_layout.addWidget( self.branch_text, row, 1 )

        self.h_filter_layout.addWidget( QtWidgets.QLabel( T_('Path:') ), row, 2 )
        self.h_filter_layout.addWidget( self.folder_text, row, 3 )

        self.h_filter_layout.setColumnStretch( 1, 1 )
        self.h_filter_layout.setColumnStretch( 3, 2 )

        self.h_filter_widget.setLayout( self.h_filter_layout )

        self.v_table_widget = QtWidgets.QWidget( self.v_split )
        self.v_table_layout = QtWidgets.QVBoxLayout()
        self.v_table_layout.addWidget( self.h_filter_widget )
        self.v_table_layout.addWidget( self.table_view )

        self.v_table_widget.setLayout( self.v_table_layout )

        self.h_split.addWidget( self.tree_view )
        self.h_split.addWidget( self.v_table_widget )

        self.v_split.addWidget( self.h_split )
        self.v_split.addWidget( self.__log.logWidget() )

        # setup selection on the tree
        selection_model = self.tree_view.selectionModel()
        selection_model.selectionChanged.connect( self.treeSelectionChanged )

        # select the first project
        bookmark = self.app.prefs.getBookmarks().getLastPosition()
        if bookmark is not None:
            index = self.tree_model.indexFromBookmark( bookmark )

        else:
            index = self.tree_model.getFirstProjectIndex()

        if index is not None:
            selection_model.select( index,
                        selection_model.Clear |
                        selection_model.Select |
                        selection_model.Current )

            self.tree_view.scrollTo( index )

        # timer used to wait for focus to be set after app is activated
        self.timer_update_enable_states = QtCore.QTimer()
        self.timer_update_enable_states.timeout.connect( self.updateActionEnabledStates )
        self.timer_update_enable_states.setSingleShot( True )

        # The rest of init has to be done after the widgets are rendered
        self.timer_init = QtCore.QTimer()
        self.timer_init.timeout.connect( self.completeStatupInitialisation )
        self.timer_init.setSingleShot( True )
        self.timer_init.start( 0 )

    def completeStatupInitialisation( self ):
        self._debug( 'completeStatupInitialisation()' )

        # set splitter position
        tree_size_ratio = 0.3
        width = sum( self.h_split.sizes() )
        tree_width = int( width * tree_size_ratio )
        table_width = width - tree_width
        self.h_split.setSizes( [tree_width, table_width] )

        self.updateActionEnabledStates()

        self.log.debug( 'Debug messages are enabled' )

        self.timer_init = None

    def setStatusText( self, text ):
        self.status_message.setText( text )

    def __setupTableViewAndModel( self ):
        self.table_model = wb_git_table_model.WbGitTableModel( self.app )

        self.table_sortfilter = wb_git_table_model.WbGitTableSortFilter( self.app )
        self.table_sortfilter.setSourceModel( self.table_model )
        self.table_sortfilter.setDynamicSortFilter( False )

        self.table_sort_column = self.table_model.col_cache
        self.table_sort_order = QtCore.Qt.AscendingOrder

        self.table_view = WbTableView( self, self.all_table_keys, self.tableKeyHandler )
        self.table_view.setModel( self.table_sortfilter )
        # allow Tab/Shift-Tab to move between tree/filter/table and log widgets
        self.table_view.setTabKeyNavigation( False )

        # set sort params
        self.table_view.sortByColumn( self.table_sort_column, self.table_sort_order )
        # and enable to apply
        self.table_view.setSortingEnabled( True )

        # always select a whole row
        self.table_view.setSelectionBehavior( self.table_view.SelectRows )
        self.table_view.doubleClicked.connect( self.tableDoubleClicked )

        # connect up signals
        self.table_view.horizontalHeader().sectionClicked.connect( self.tableHeaderClicked )
        self.table_view.customContextMenuRequested.connect( self.tableContextMenu )
        self.table_view.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )

        # size columns
        char_width = 10
        self.table_view.setColumnWidth( self.table_model.col_cache, char_width*4 )
        self.table_view.setColumnWidth( self.table_model.col_working, char_width*4 )
        self.table_view.setColumnWidth( self.table_model.col_name, char_width*32 )
        self.table_view.setColumnWidth( self.table_model.col_date, char_width*16 )
        self.table_view.setColumnWidth( self.table_model.col_type, char_width*6 )

    def __setupTreeViewAndModel( self ):
        self.tree_model = wb_git_tree_model.WbGitTreeModel( self.app, self.table_model )

        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setModel( self.tree_model )
        self.tree_view.setExpandsOnDoubleClick( True )

        # connect up signals
        self.tree_view.customContextMenuRequested.connect( self.treeContextMenu )
        self.tree_view.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )

    def updateActionEnabledStates( self ):
        self.updateEnableStates()

        if self.commit_dialog is not None:
            git_project = self.__treeSelectedGitProject()
            self.commit_dialog.setStatus(
                    git_project.getReportStagedFiles(),
                    git_project.getReportUntrackedFiles() )

    def setupMenuBar( self, mb ):
        m = mb.addMenu( T_('&File') )
        self._addMenu( m, T_('&Preferences…'), self.appActionPreferences, role=QtWidgets.QAction.PreferencesRole )
        self._addMenu( m, T_('&Prefs…'), self.appActionPreferences )
        self._addMenu( m, T_('E&xit'), self.close, role=QtWidgets.QAction.QuitRole )

        m = mb.addMenu( T_('F&older Actions') )
        self._addMenu( m, T_('&Command Shell'), self.treeActionShell, self.enablerFolderExists, 'toolbar_images/terminal.png' )
        self._addMenu( m, T_('&File Browser'), self.treeActionFileBrowse, self.enablerFolderExists, 'toolbar_images/file_browser.png' )

        m = mb.addMenu( T_('File &Actions') )
        self._addMenu( m, T_('Edit'), self.tableActionEdit, self.enablerFilesExists, 'toolbar_images/edit.png' )
        self._addMenu( m, T_('Open'), self.tableActionOpen, self.enablerFilesExists, 'toolbar_images/open.png' )

        m = mb.addMenu( T_('&Information') )
        self._addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionGitDiffHeadVsWorking, self.enablerDiffHeadVsWorking, 'toolbar_images/diff.png' )
        self._addMenu( m, T_('Diff Staged vs. Working'), self.treeTableActionGitDiffStagedVsWorking, self.enablerDiffStagedVsWorking, 'toolbar_images/diff.png' )
        self._addMenu( m, T_('Diff HEAD vs. Staged'), self.treeTableActionGitDiffHeadVsStaged, self.enablerDiffHeadVsStaged, 'toolbar_images/diff.png' )
        m.addSeparator()
        self._addMenu( m, T_('Status'), self.treeActionGitStatus )

        m = mb.addMenu( T_('&Git Actions') )
        self._addMenu( m, T_('Stage'), self.tableActionGitStage, self.enablerFilesStage, 'toolbar_images/include.png' )
        self._addMenu( m, T_('Unstage'), self.tableActionGitUnstage, self.enablerFilesUnstage, 'toolbar_images/exclude.png' )
        self._addMenu( m, T_('Revert'), self.tableActionGitRevert, self.enablerFilesRevert, 'toolbar_images/revert.png' )
        m.addSeparator()
        self._addMenu( m, T_('Delete…'), self.tableActionGitDelete, self.enablerFilesExists )
        m.addSeparator()
        self._addMenu( m, T_('Commit…'), self.treeActionCommit, self.enablerCommit, 'toolbar_images/commit.png' )

        m.addSeparator()
        self._addMenu( m, T_('Push…'), self.treeActionPush, self.enablerPush, 'toolbar_images/push.png' )
        self._addMenu( m, T_('Pull…'), self.treeActionPull, icon_name='toolbar_images/pull.png' )

        m = mb.addMenu( T_('&Project') )
        self._addMenu( m, T_('Add…'), self.projectActionAdd )
        self._addMenu( m, T_('Settings…'), self.projectActionSettings, self.enablerIsProject )
        self._addMenu( m, T_('Delete'), self.projectActionDelete, self.enablerIsProject )

        m = mb.addMenu( T_('&Help' ) )
        self._addMenu( m, T_("&About…"), self.appActionAbout )

    def __setupTreeContextMenu( self ):
        m = self.tree_context_menu = QtWidgets.QMenu( self )
        m.addSection( T_('Folder Actions') )
        self._addMenu( m, T_('&Command Shell'), self.treeActionShell, self.enablerFolderExists, 'toolbar_images/terminal.png' )
        self._addMenu( m, T_('&File Browser'), self.treeActionFileBrowse, self.enablerFolderExists, 'toolbar_images/file_browser.png' )

    def __setupTableContextMenu( self ):
        m = self.table_context_menu = QtWidgets.QMenu( self )

        m.addSection( T_('File Actions') )
        self._addMenu( m, T_('Edit'), self.tableActionEdit, self.enablerFilesExists, 'toolbar_images/edit.png' )
        self._addMenu( m, T_('Open'), self.tableActionOpen, self.enablerFilesExists, 'toolbar_images/open.png' )

        m.addSection( T_('Diff') )
        self._addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionGitDiffHeadVsWorking, self.enablerDiffHeadVsWorking, 'toolbar_images/diff.png' )
        self._addMenu( m, T_('Diff Staged vs. Working'), self.treeTableActionGitDiffStagedVsWorking, self.enablerDiffStagedVsWorking, 'toolbar_images/diff.png' )
        self._addMenu( m, T_('Diff HEAD vs. Staged'), self.treeTableActionGitDiffHeadVsStaged, self.enablerDiffHeadVsStaged, 'toolbar_images/diff.png' )

        m.addSection( T_('Git Actions') )
        self._addMenu( m, T_('Stage'), self.tableActionGitStage, self.enablerFilesStage, 'toolbar_images/include.png' )
        self._addMenu( m, T_('Unstage'), self.tableActionGitUnstage, self.enablerFilesUnstage, 'toolbar_images/exclude.png' )
        self._addMenu( m, T_('Revert'), self.tableActionGitRevert, self.enablerFilesRevert, 'toolbar_images/revert.png' )
        m.addSeparator()
        self._addMenu( m, T_('Delete…'), self.tableActionGitDelete, self.enablerFilesExists )

    def setupToolBar( self ):
        style = self.style()

        t = self.tool_bar_tree = self._addToolBar( T_('tree') )
        self._addTool( t, T_('Command Shell'), self.treeActionShell, self.enablerFolderExists, 'toolbar_images/terminal.png' )
        self._addTool( t, T_('File Browser'), self.treeActionFileBrowse, self.enablerFolderExists, 'toolbar_images/file_browser.png' )

        t = self.tool_bar_table = self._addToolBar( T_('table') )
        self._addTool( t, T_('Edit'), self.tableActionEdit, self.enablerFilesExists, 'toolbar_images/edit.png' )
        self._addTool( t, T_('Open'), self.tableActionOpen, self.enablerFilesExists, 'toolbar_images/open.png' )

        t = self.tool_bar_git_info = self._addToolBar( T_('git info') )
        self._addTool( t, T_('Diff'), self.treeTableActionGitDiffSmart, self.enablerDiffSmart, 'toolbar_images/diff.png' )
        self._addTool( t, T_('Commit History'), self.treeTableActionGitLogHistory, self.enablerLogHistory, 'toolbar_images/history.png' )

        t = self.tool_bar_git_state = self._addToolBar( T_('git state') )
        self._addTool( t, T_('Stage'), self.tableActionGitStage, self.enablerFilesStage, 'toolbar_images/include.png' )
        self._addTool( t, T_('Unstage'), self.tableActionGitUnstage, self.enablerFilesUnstage, 'toolbar_images/exclude.png' )
        self._addTool( t, T_('Revert'), self.tableActionGitRevert, self.enablerFilesRevert, 'toolbar_images/revert.png' )
        t.addSeparator()
        self._addTool( t, T_('Commit'), self.treeActionCommit, self.enablerCommit, 'toolbar_images/commit.png' )
        t.addSeparator()
        self._addTool( t, T_('Push'), self.treeActionPush, self.enablerPush, 'toolbar_images/push.png' )
        self._addTool( t, T_('Pull'), self.treeActionPull, icon_name='toolbar_images/pull.png' )

    def setupStatusBar( self, s ):
        self.status_message = QtWidgets.QLabel()
        s.addWidget( self.status_message )

    #------------------------------------------------------------
    #
    #   Enabler handlers
    #
    #------------------------------------------------------------
    def enablerFolderExists( self, cache ):
        key = 'enablerFolderExists'
        if key not in cache:
            cache[ key ] = self.__treeSelectedAbsoluteFolder()

        return cache[ key ] is not None

    def enablerIsProject( self, cache ):
        key = 'enablerIsProject'
        if key not in cache:
            cache[ key ] = self.__treeSelectedRelativeFolder() == pathlib.Path( '.' )

        return cache[ key ]

    def enablerFilesExists( self, cache ):
        key = 'enablerFilesExists'
        if key not in cache:
            cache[ key ] = self.__tableSelectedExistingFiles()

        return len( cache[ key ] ) > 0

    def enablerFilesStage( self, cache ):
        key = 'enablerFilesStage'
        if key not in cache:
            #with_status = (pygit2.GIT_STATUS_WT_MODIFIED|pygit2.GIT_STATUS_WT_NEW|pygit2.GIT_STATUS_WT_DELETED)
            #cache[ key ] = self.__tableSelectedWithStatus( with_status, 0 )
            cache[ key ] = True

        return cache[ key ]

    def enablerFilesUnstage( self, cache ):
        key = 'enablerFilesUnstage'
        if key not in cache:
            #with_status = pygit2.GIT_STATUS_INDEX_MODIFIED|pygit2.GIT_STATUS_INDEX_NEW|pygit2.GIT_STATUS_INDEX_DELETED
            #cache[ key ] = self.__tableSelectedWithStatus( with_status, 0 )
            cache[ key ] = True

        return cache[ key ]

    def enablerFilesRevert( self, cache ):
        key = 'enablerFilesRevert'
        if key not in cache:
            #with_status = pygit2.GIT_STATUS_WT_MODIFIED|pygit2.GIT_STATUS_WT_DELETED
            #without_status = pygit2.GIT_STATUS_INDEX_MODIFIED
            #cache[ key ] = self.__tableSelectedWithStatus( with_status, without_status )
            cache[ key ] = True

        return cache[ key ]

    def __enablerFocusWidget( self, cache ):
        key = '__enablerFocusWidget'
        if key not in cache:
            if self.tree_view.hasFocus():
                cache[ key ] = 'tree'

            elif( self.table_view.hasFocus()
            or self.filter_text.hasFocus() ):
                cache[ key ] = 'table'

            else:
                cache[ key ] = None

        return cache[ key ]

    def __enablerTableSelectedStatus( self, cache ):
        key = '__enablerTableSelectedStatus'
        if key not in cache:
            cache[ key ] = self.__tableSelectedStatus()

        return cache[ key ]

    def __enablerDiff( self, cache, key, predicate ):
        if key not in cache:
            focus = self.__enablerFocusWidget( cache )
            if focus == 'tree':
                cache[ key ] = True

            elif focus == 'table':
                # make sure all the selected entries is modified
                all_file_states = self.__enablerTableSelectedStatus( cache )
                enable = True
                for obj in all_file_states:
                    if not predicate( obj ):
                        enable = False
                        break

                cache[ key ] = enable

            else:
                cache[ key ] = False

        return cache[ key ]

    def enablerDiffHeadVsWorking( self, cache ):
        return self.__enablerDiff( cache, 'enablerDiffHeadVsWorking', wb_git_project.WbGitFileState.canDiffHeadVsWorking )

    def enablerDiffStagedVsWorking( self, cache ):
        return self.__enablerDiff( cache, 'enablerDiffStagedVsWorking', wb_git_project.WbGitFileState.canDiffStagedVsWorking )

    def enablerDiffHeadVsStaged( self, cache ):
        return self.__enablerDiff( cache, 'enablerDiffHeadVsStaged', wb_git_project.WbGitFileState.canDiffHeadVsStaged )

    def enablerDiffSmart( self, cache ):
        key = 'enablerDiffSmart'
        if key not in cache:
            focus = self.__enablerFocusWidget( cache )
            if focus == 'tree':
                cache[ key ] = True

            elif focus == 'table':
                # make sure all the selected entries is modified
                all_file_states = self.__enablerTableSelectedStatus( cache )
                enable = True
                for obj in all_file_states:
                    if not (obj.canDiffStagedVsWorking()
                            or obj.canDiffHeadVsWorking()
                            or obj.canDiffHeadVsStaged()):
                        enable = False
                        break

                cache[ key ] = enable

            else:
                cache[ key ] = False

        return cache[ key ]

    def enablerCommit( self, cache ):
        key = 'enablerCommit'
        if key not in cache:
            # enable if any files staged
            git_project = self.__treeSelectedGitProject()

            can_commit = False
            if( git_project is not None
            and self.commit_dialog is None
            and git_project.numStagedFiles() > 0 ):
                can_commit = True

            cache[ key ] = can_commit

        return cache[ key ]

    def enablerPush( self, cache ):
        key = 'enablerPush'
        if key not in cache:
            git_project = self.__treeSelectedGitProject()
            cache[ key ] = git_project.canPush()

        return cache[ key ]

    def enablerLogHistory( self, cache ):
        return True

    #------------------------------------------------------------
    #
    #   Event handlers
    #
    #------------------------------------------------------------
    def appActiveHandler( self ):
        self._debug( 'appActiveHandler()' )

        # update the selected projects data
        self.tree_model.appActiveHandler()

        # sort filter is now invalid
        self.table_sortfilter.invalidate()

        # enabled states will have changed
        self.timer_update_enable_states.start( 0 )

    #------------------------------------------------------------
    #
    # app actions
    #
    #------------------------------------------------------------
    def appActionPreferences( self ):
        pref_dialog = wb_git_preferences_dialog.WbGitPreferencesDialog( self.app, self )
        if pref_dialog.exec_():
            pref_dialog.savePreferences()
            self.app.writePreferences()

    def appActionQqq( self ):
        print( 'qqq menu qqq' )

    def appActionAbout( self ):
        from PyQt5 import Qt
        all_about_info = []
        all_about_info.append( "%s %d.%d.%d-%d" %
                                (' '.join( self.app.app_name_parts )
                                ,wb_git_version.major, wb_git_version.minor
                                ,wb_git_version.patch, wb_git_version.build) )
        all_about_info.append( 'Python %d.%d.%d %s %d' %
                                (sys.version_info.major
                                ,sys.version_info.minor
                                ,sys.version_info.micro
                                ,sys.version_info.releaselevel
                                ,sys.version_info.serial) )
        all_about_info.append( 'PyQt %s, Qt %s' % (Qt.PYQT_VERSION_STR, QtCore.QT_VERSION_STR) )
        all_about_info.append( T_('Copyright Barry Scott (c) 2016-%s. All rights reserved') % (wb_git_version.year,) )

        QtWidgets.QMessageBox.information( self,
            T_('About %s') % (' '.join( self.app.app_name_parts ),),
            '\n'.join( all_about_info ) )

    def closeEvent( self, event ):
        self.appActionClose( close=False )

    def appActionClose( self, close=True ):
        self._debug( 'appActionClose()' )
        git_project_tree_node = self.tree_model.selectedGitProjectTreeNode()

        if git_project_tree_node is not None:
            prefs = self.app.prefs.getBookmarks()
            bookmark = wb_git_preferences.Bookmark(
                        prefs.name_last_position,
                        git_project_tree_node.project.projectName(),
                        git_project_tree_node.relativePath() )

            prefs.addBookmark( bookmark )

        win_prefs = self.app.prefs.getWindow()
        win_prefs.setFrameGeometry( self.saveGeometry().toHex().data() )

        self.app.writePreferences()

        # close all open modeless windows
        wb_diff_unified_view.WbDiffViewBase.closeAllWindows()
        wb_git_log_history.WbGitLogHistoryView.closeAllWindows()
        wb_git_status_view.WbGitStatusView.closeAllWindows()

        if close:
            self.close()


    #------------------------------------------------------------
    #
    # project actions
    #
    #------------------------------------------------------------
    def projectActionAdd( self ):
        wiz = wb_git_project_dialogs.WbGitAddProjectWizard( self.app )
        if wiz.exec_():
            if wiz.git_url is None:
                prefs = self.app.prefs.getProjects()
                project = wb_git_preferences.Project( wiz.name, wiz.wc_path )
                prefs.addProject( project )

                self.app.writePreferences()

                self.tree_model.addProject( project )
                index = self.tree_model.indexFromProject( project )

                selection_model = self.tree_view.selectionModel()
                selection_model.select( index,
                            selection_model.Clear |
                            selection_model.Select |
                            selection_model.Current )

                self.tree_view.scrollTo( index )

    def projectActionDelete( self ):
        project_name = self.__treeSelectedProjectName()

        default_button = QtWidgets.QMessageBox.No

        title = T_('Confirm Delete Project')
        message = T_('Are you sure you wish to delete project %s') % (project_name,)

        rc = QtWidgets.QMessageBox.question( self, title, message, defaultButton=default_button )
        if rc == QtWidgets.QMessageBox.Yes:
            prefs = self.app.prefs.getProjects()
            # remove from preferences
            prefs.delProject( project_name )
            self.app.writePreferences()

            # remove from the tree model
            self.tree_model.delProject( project_name )

            # setup on a new selection
            index = self.tree_model.getFirstProjectIndex()

            if index is not None:
                selection_model = self.tree_view.selectionModel()
                selection_model.select( index,
                            selection_model.Clear |
                            selection_model.Select |
                            selection_model.Current )

            self.tree_view.scrollTo( index )

    def projectActionSettings( self ):
        pass

    #------------------------------------------------------------
    #
    # tree or table actions depending on focus
    #
    #------------------------------------------------------------
    def __callTreeOrTableFunction( self, fn_tree, fn_table ):
        if self.tree_view.hasFocus():
            fn_tree()

        elif( self.table_view.hasFocus()
        or self.filter_text.hasFocus() ):
            fn_table()

        # else in log so ignore

    def treeTableActionGitDiffSmart( self ):
        self.__callTreeOrTableFunction( self.treeActionGitDiffSmart, self.tableActionGitDiffSmart )

    def treeTableActionGitDiffStagedVsWorking( self ):
        self.__callTreeOrTableFunction( self.treeActionGitDiffStagedVsWorking, self.tableActionGitDiffStagedVsWorking )

    def treeTableActionGitDiffHeadVsStaged( self ):
        self.__callTreeOrTableFunction( self.treeActionGitDiffHeadVsStaged, self.tableActionGitDiffHeadVsStaged )

    def treeTableActionGitDiffHeadVsWorking( self ):
        self.__callTreeOrTableFunction( self.treeActionGitDiffHeadVsWorking, self.tableActionGitDiffHeadVsWorking )

    def treeTableActionGitLogHistory( self ):
        self.__callTreeOrTableFunction( self.treeActionGitLogHistory, self.tableActionGitLogHistory )

    #------------------------------------------------------------
    #
    # tree actions
    #
    #------------------------------------------------------------
    def __treeSelectedProjectName( self ):
        # only correct is called with the top of the tree is selected
        # which is ensured by the enablers
        git_project_tree_node = self.tree_model.selectedGitProjectTreeNode()
        if git_project_tree_node is None:
            return None

        return git_project_tree_node.name

    def __treeSelectedAbsoluteFolder( self ):
        git_project_tree_node = self.tree_model.selectedGitProjectTreeNode()
        if git_project_tree_node is None:
            return None

        folder_path = git_project_tree_node.absolutePath()

        if not folder_path.exists():
            return None

        return folder_path

    def __treeSelectedRelativeFolder( self ):
        git_project_tree_node = self.tree_model.selectedGitProjectTreeNode()
        if git_project_tree_node is None:
            return None

        return git_project_tree_node.relativePath()

    def __treeSelectedGitProject( self ):
        git_project_tree_node = self.tree_model.selectedGitProjectTreeNode()
        if git_project_tree_node is None:
            return None

        return git_project_tree_node.project

    def treeContextMenu( self, pos ):
        self._debug( 'treeContextMenu( %r )' % (pos,) )
        global_pos = self.tree_view.viewport().mapToGlobal( pos )

        self.tree_context_menu.exec_( global_pos )

    def treeSelectionChanged( self, selected, deselected ):
        self.filter_text.clear()
        self.tree_model.selectionChanged( selected, deselected )
        self.updateActionEnabledStates()

        git_project = self.__treeSelectedGitProject()
        if git_project is None:
            self.branch_text.clear()

        else:
            self.branch_text.setText( git_project.headRefName() )

        folder = self.__treeSelectedAbsoluteFolder()
        if folder is None:                                                          
             self.folder_text.clear()

        else:
            try:
                # try to convert to ~ form
                folder = folder.relative_to( pathlib.Path( os.environ['HOME'] ) )
                folder = '~/%s' % (folder,)

            except ValueError:
                folder = str( folder )

            self.folder_text.setText( folder )

    def treeActionShell( self ):
        folder_path = self.__treeSelectedAbsoluteFolder()
        if folder_path is None:
            return

        wb_shell_commands.CommandShell( self.app, folder_path )

    def treeActionFileBrowse( self ):
        folder_path = self.__treeSelectedAbsoluteFolder()
        if folder_path is None:
            return

        wb_shell_commands.FileBrowser( self.app, folder_path )

    def treeActionGitDiffSmart( self ):
        self._debug( 'treeActionGitDiffSmart()' )

    def treeActionGitDiffStagedVsWorking( self ):
        self._debug( 'treeActionGitDiffStagedVsWorking()' )

    def treeActionGitDiffHeadVsStaged( self ):
        self._debug( 'treeActionGitDiffHeadVsStaged()' )

    def treeActionGitDiffHeadVsWorking( self ):
        self._debug( 'treeActionGitDiffHeadVsWorking()' )

    def treeActionCommit( self ):
        git_project = self.__treeSelectedGitProject()

        self.commit_dialog = wb_git_commit_dialog.WbGitCommitDialog(
                    self.app, self,
                    T_('Commit %s') % (git_project.projectName(),) )
        self.commit_dialog.setStatus(
                    git_project.getReportStagedFiles(),
                    git_project.getReportUntrackedFiles() )
        self.commit_dialog.finished.connect( self.__commitDialogFinished )

        # show to the user
        self.commit_dialog.show()


    def __commitDialogFinished( self, result ):
        if result:
            git_project = self.__treeSelectedGitProject()
            message = self.commit_dialog.getMessage()
            commit_id = git_project.cmdCommit( message )

            # take account of the change
            self.tree_model.refreshTree()

            # sort filter is now invalid
            self.table_sortfilter.invalidate()

            # enabled states will have changed
            self.updateActionEnabledStates()

            headline = message.split('\n')[0]

            self.log.info( T_('Committed "%(headline)s" as %(commit_id)s') % {'headline': headline, 'commit_id': commit_id} )

        self.commit_dialog = None

        # enabled states may have changed
        self.updateActionEnabledStates()

    # ------------------------------------------------------------
    def __logGitCommandError( self, e ):
        self.log.error( "'%s' returned with exit code %i" %
                        (' '.join(str(i) for i in e.command), e.status) )
        if e.stderr:
            all_lines = e.stderr.split('\n')
            if all_lines[-1] == '':
                del all_lines[-1]

            for line in all_lines:
                self.log.error( line )

    def treeActionPush( self ):
        git_project = self.__treeSelectedGitProject().newInstance()
        self.setStatusText( 'Push…' )

        self.app.backgroundProcess( self.treeActionPushBg, (git_project,) )

    def treeActionPushBg( self, git_project ):
        try:
            git_project.cmdPush( self.pushProgressHandlerBg, self.pushInfoHandlerBg )

        except wb_git_project.GitCommandError as e:
            self.__logGitCommandError( e )

        self.app.foregroundProcess( self.setStatusText, ('',) )
        self.app.foregroundProcess( self.updateActionEnabledStates, () )

    def pushInfoHandlerBg( self, info ):
        self.app.foregroundProcess( self.pushInfoHandler, (info,) )

    def pushInfoHandler( self, info ):
        self.log.info( 'Push summary: %s' % (info.summary,) )

    def pushProgressHandlerBg( self, is_begin, is_end, stage_name, cur_count, max_count, message ):
        self.app.foregroundProcess( self.pushProgressHandler, (is_begin, is_end, stage_name, cur_count, max_count, message) )

    def pushProgressHandler( self, is_begin, is_end, stage_name, cur_count, max_count, message ):
        if type(cur_count) in (int,float):
            if type(max_count) in (int,float):
                status = 'Push %s %d/%d' % (stage_name, int(cur_count), int(max_count))

            else:
                status = 'Push %s %d' % (stage_name, int(cur_count))

        else:
            status = 'Push %s' % (stage_name,)

        if message != '':
            status = '%s - %s' % (status, message)
           
        self.setStatusText( status )
        if is_end:
            self.log.info( status )

    # ------------------------------------------------------------
    def treeActionPull( self ):
        git_project = self.__treeSelectedGitProject().newInstance()
        self.setStatusText( 'Pull...' )

        self.app.backgroundProcess( self.treeActionPullBg, (git_project,) )

    def treeActionPullBg( self, git_project ):
        try:
            git_project.cmdPull( self.pullProgressHandlerBg, self.pullInfoHandlerBg )

        except wb_git_project.GitCommandError as e:
            self.__logGitCommandError( e )

        self.app.foregroundProcess( self.setStatusText, ('',) )
        self.app.foregroundProcess( self.updateActionEnabledStates, () )

    def pullInfoHandlerBg( self, info ):
        self.app.foregroundProcess( self.pullInfoHandler, (info,) )

    def pullInfoHandler( self, info ):
        if info.note != '':
            self.log.info( 'Pull Note: %s' % (info.note,) )

        for state, state_name in (
                    (info.NEW_TAG, T_('New tag')),
                    (info.NEW_HEAD, T_('New head')),
                    (info.HEAD_UPTODATE, T_('Head up to date')),
                    (info.TAG_UPDATE, T_('Tag update')),
                    (info.FORCED_UPDATE, T_('Forced update')),
                    (info.FAST_FORWARD, T_('Fast forward')),
                    ):
            if (info.flags&state) != 0:
                self.log.info( T_('Pull status: %(state_name)s for %(name)s') % {'state_name': state_name, 'name': info.name} )

        for state, state_name in (
                    (info.REJECTED, T_('Rejected')),
                    (info.ERROR, T_('Error'))
                    ):
            if (info.flags&state) != 0:
                self.log.error( T_('Pull status: %(state_name)s') % {'state_name': state_name} )

    def pullProgressHandlerBg( self, is_begin, is_end, stage_name, cur_count, max_count, message ):
        self.app.foregroundProcess( self.pullProgressHandler, (is_begin, is_end, stage_name, cur_count, max_count, message) )

    def pullProgressHandler( self, is_begin, is_end, stage_name, cur_count, max_count, message ):
        if type(cur_count) in (int,float):
            if type(max_count) in (int,float):
                status = 'Pull %s %d/%d' % (stage_name, int(cur_count), int(max_count))

            else:
                status = 'Pull %s %d' % (stage_name, int(cur_count))

        else:
            status = 'Push %s' % (stage_name,)

        if message != '':
            status = '%s - %s' % (status, message)
           
        self.setStatusText( status )
        if is_end:
            self.log.info( status )

    # ------------------------------------------------------------
    def treeActionGitLogHistory( self ):
        options = wb_git_log_history.WbGitLogHistoryOptions( self.app, self )

        if options.exec_():
            git_project = self.__treeSelectedGitProject()

            commit_log_view = wb_git_log_history.WbGitLogHistoryView(
                    self.app,
                    T_('Commit Log for %s') % (git_project.projectName(),),
                    wb_git_images.getQIcon( 'wb.png' ) )
            commit_log_view.showCommitLogForRepository( git_project, options )
            commit_log_view.show()

    def treeActionGitStatus( self ):
        git_project = self.__treeSelectedGitProject()

        commit_status_view = wb_git_status_view.WbGitStatusView(
                self.app,
                T_('Status for %s') % (git_project.projectName(),),
                wb_git_images.getQIcon( 'wb.png' ) )
        commit_status_view.setStatus(
                    git_project.getUnpushedCommits(),
                    git_project.getReportStagedFiles(),
                    git_project.getReportUntrackedFiles() )
        commit_status_view.show()

    #------------------------------------------------------------
    #
    # table actions
    #
    #------------------------------------------------------------
    def __tableSelectedFiles( self ):
        return [index.data( QtCore.Qt.UserRole ).name
                    for index in self.table_view.selectedIndexes()
                    if index.column() == 0]

    def __tableSelectedExistingFiles( self ):
        folder_path = self.__treeSelectedAbsoluteFolder()
        if folder_path is None:
            return []

        all_filenames = [folder_path / name for name in self.__tableSelectedFiles()]
        all_existing_filenames = [filename for filename in all_filenames if filename.exists()]
        return all_existing_filenames

    def __tableSelectedWithStatus( self, with_status, without_status ):
        folder_path = self.__treeSelectedAbsoluteFolder()
        if folder_path is None:
            return False

        all_names = self.__tableSelectedFiles()
        if len(all_names) == 0:
            return False

        git_project = self.__treeSelectedGitProject()

        relative_folder = self.__treeSelectedRelativeFolder()

        for name in all_names:
            status = git_project.getStatus( relative_folder / name )
            if (status&with_status) == 0:
                return False

            if (status&without_status) != 0:
                return False

        return True

    def __tableSelectedStatus( self ):
        folder_path = self.__treeSelectedAbsoluteFolder()
        if folder_path is None:
            return []

        all_names = self.__tableSelectedFiles()
        if len(all_names) == 0:
            return []

        git_project = self.__treeSelectedGitProject()

        relative_folder = self.__treeSelectedRelativeFolder()

        return [git_project.getFileState( relative_folder / name ) for name in all_names]

    def tableKeyHandler( self, key ):
        if key in self.table_keys_edit:
            self.tableActionEdit()

        elif key in self.table_keys_open:
            self.tableActionOpen()

    def tableContextMenu( self, pos ):
        self._debug( 'tableContextMenu( %r )' % (pos,) )
        global_pos = self.table_view.viewport().mapToGlobal( pos )

        self.table_context_menu.exec_( global_pos )

    def tableHeaderClicked( self, column ):
        if column == self.table_sort_column:
            if self.table_sort_order == QtCore.Qt.DescendingOrder:
                self.table_sort_order = QtCore.Qt.AscendingOrder
            else:
                self.table_sort_order = QtCore.Qt.DescendingOrder

        else:
            self.table_sort_column = column
            self.table_sort_order = QtCore.Qt.AscendingOrder

        self.table_view.sortByColumn( self.table_sort_column, self.table_sort_order )

    def tableDoubleClicked( self, index ):
        self.tableActionEdit()

    def tableActionOpen( self ):
        all_filenames = self.__tableSelectedExistingFiles()
        if len(all_filenames) > 0:
            wb_shell_commands.ShellOpen( self.app, self.__treeSelectedAbsoluteFolder(), all_filenames )

    def tableActionEdit( self ):
        all_filenames = self.__tableSelectedExistingFiles()
        if len(all_filenames) > 0:
            wb_shell_commands.EditFile( self.app, self.__treeSelectedAbsoluteFolder(), all_filenames )

    def tableActionGitStage( self ):
        self.__tableActionChangeRepo( self.__areYouSureAlways, self.__actionGitStage )

    def tableActionGitUnstage( self ):
        self.__tableActionChangeRepo( self.__areYouSureAlways, self.__actionGitUnStage )

    def tableActionGitRevert( self ):
        self.__tableActionChangeRepo( self.__areYouSureRevert, self.__actionGitRevert )

    def tableActionGitDelete( self ):
        self.__tableActionChangeRepo( self.__areYouSureDelete, self.__actionGitDelete )

    def tableActionGitDiffSmart( self ):
        self._debug( 'tableActionGitDiffSmart()' )
        self.__tableActionViewRepo( self.__areYouSureAlways, self.__actionGitDiffSmart )

    def tableActionGitDiffStagedVsWorking( self ):
        self._debug( 'tableActionGitDiffStagedVsWorking()' )
        self.__tableActionViewRepo( self.__areYouSureAlways, self.__actionGitDiffStagedVsWorking )

    def tableActionGitDiffHeadVsStaged( self ):
        self._debug( 'tableActionGitDiffHeadVsStaged()' )
        self.__tableActionViewRepo( self.__areYouSureAlways, self.__actionGitDiffHeadVsStaged )

    def tableActionGitDiffHeadVsWorking( self ):
        self._debug( 'tableActionGitDiffHeadVsWorking()' )
        self.__tableActionViewRepo( self.__areYouSureAlways, self.__actionGitDiffHeadVsWorking )

    def tableActionGitLogHistory( self ):
        self.__tableActionViewRepo( self.__areYouSureAlways, self.__actionGitLogHistory )

    def __actionGitStage( self, git_project, filename ):
        git_project.cmdStage( filename )

    def __actionGitUnStage( self, git_project, filename ):
        git_project.cmdUnstage( 'HEAD', filename )
        pass

    def __actionGitRevert( self, git_project, filename ):
        git_project.cmdRevert( 'HEAD', filename )

    def __actionGitDelete( self, git_project, filename ):
        git_project.cmdDelete( filename )

    def __actionGitDiffSmart( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        if file_state.canDiffStagedVsWorking():
            self.__actionGitDiffStagedVsWorking( git_project, filename )

        elif file_state.canDiffHeadVsStaged():
            self.__actionGitDiffHeadVsStaged( git_project, filename )

        elif file_state.canDiffHeadVsWorking():
            self.__actionGitDiffHeadVsWorking( git_project, filename )

    def __diffUnified( self, old_lines, new_lines ):
        return list( difflib.unified_diff( old_lines, new_lines ) )

    def __actionGitDiffHeadVsWorking( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        old_lines = file_state.getTextLinesHead()
        new_lines = file_state.getTextLinesWorking()

        text = self.__diffUnified( old_lines, new_lines )
        title = T_('Diff HEAD vs. Work %s') % (filename,)

        window = wb_diff_unified_view.WbDiffViewText( self.app, title, wb_git_images.getQIcon( 'wb.png' ) )
        window.setUnifiedDiffText( text )
        window.show()

    def __actionGitDiffStagedVsWorking( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        old_lines = file_state.getTextLinesStaged()
        new_lines = file_state.getTextLinesWorking()

        text = self.__diffUnified( old_lines, new_lines )
        title = T_('Diff Staged vs. Work %s') % (filename,)

        window = wb_diff_unified_view.WbDiffViewText( self.app, title, wb_git_images.getQIcon( 'wb.png' ) )
        window.setUnifiedDiffText( text )
        window.show()

    def __actionGitDiffHeadVsStaged( self, git_project, filename ):
        file_state = git_project.getFileState( filename )

        old_lines = file_state.getTextLinesHead()
        new_lines = file_state.getTextLinesStaged()

        text = self.__diffUnified( old_lines, new_lines )
        title = T_('Diff HEAD vs. Staged %s') % (filename,)

        window = wb_diff_unified_view.WbDiffViewText( self.app, title, wb_git_images.getQIcon( 'wb.png' ) )
        window.setUnifiedDiffText( text )
        window.show()

    def __actionGitLogHistory( self, git_project, filename ):
        options = wb_git_log_history.WbGitLogHistoryOptions( self.app, self )

        if options.exec_():
            commit_log_view = wb_git_log_history.WbGitLogHistoryView(
                    self.app, T_('Commit Log for %s') % (filename,), wb_git_images.getQIcon( 'wb.png' ) )

            commit_log_view.showCommitLogForFile( git_project, filename, options )
            commit_log_view.show()

    #------------------------------------------------------------
    def __areYouSureAlways( self, all_filenames ):
        return True

    def __areYouSureRevert( self, all_filenames ):
        default_button = QtWidgets.QMessageBox.No

        title = T_('Confirm Revert')
        all_parts = [T_('Are you sure you wish to revert:')]
        all_parts.extend( [str(filename) for filename in all_filenames] )

        message = '\n'.join( all_parts )

        rc = QtWidgets.QMessageBox.question( self, title, message, defaultButton=default_button )
        return rc == QtWidgets.QMessageBox.Yes

    def __areYouSureDelete( self, all_filenames ):
        default_button = QtWidgets.QMessageBox.No

        title = T_('Confirm Delete')
        all_parts = [T_('Are you sure you wish to delete:')]
        all_parts.extend( [str(filename) for filename in all_filenames] )

        message = '\n'.join( all_parts )

        rc = QtWidgets.QMessageBox.question( self, title, message, defaultButton=default_button )
        return rc == QtWidgets.QMessageBox.Yes

    def __tableActionViewRepo( self, are_you_sure_function, execute_function ):
        folder_path = self.__treeSelectedAbsoluteFolder()
        if folder_path is None:
            return

        all_names = self.__tableSelectedFiles()
        if len(all_names) == 0:
            return

        git_project = self.__treeSelectedGitProject()

        relative_folder = self.__treeSelectedRelativeFolder()

        all_filenames = [relative_folder / name for name in all_names]

        if not are_you_sure_function( all_filenames ):
            return False

        for filename in all_filenames:
            execute_function( git_project, filename )

        return True

    def __tableActionChangeRepo( self, are_you_sure_function, execute_function ):
        if self.__tableActionViewRepo( are_you_sure_function, execute_function ):
            git_project = self.__treeSelectedGitProject()
            git_project.saveChanges()

            # take account of the change
            self.table_model.refreshTable()

            # sort filter is now invalid
            self.table_sortfilter.invalidate()

            # enabled states will have changed
            self.updateActionEnabledStates()

class WbTableView(QtWidgets.QTableView):
    def __init__( self, main_window, all_keys, key_handler ):
        self.main_window = main_window
        self.all_keys = all_keys
        self.key_handler = key_handler

        self._debug = main_window._debug

        super().__init__()

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbTableView.selectionChanged()' )

        self.main_window.updateActionEnabledStates()

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )

    def keyPressEvent( self, event ):
        text = event.text()
        if text != '' and text in self.all_keys:
            self.key_handler( text )

        else:
            super().keyPressEvent( event )

    def keyReleaseEvent( self, event ):
        text = event.text()

        if text != '' and text in self.all_keys:
            return

        else:
            super().keyReleaseEvent( event )
