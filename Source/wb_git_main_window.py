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

# On OS X the packager missing this import
import sip

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import pygit2

import wb_git_version
import wb_git_images
import wb_git_preferences
#import wb_git_preferences_dialog
import wb_git_commit_dialog
import wb_git_config

import wb_git_tree_model
import wb_git_table_model
import wb_git_project

import wb_shell_commands
import wb_logging
import wb_diff_view

class WbGitMainWindow(QtWidgets.QMainWindow):
    def __init__( self, app ):
        self.app = app
        self.log = self.app.log
        self._debug = app._debugMainWindow

        # need to fix up how this gets translated
        title = T_( ' '.join( self.app.app_name_parts ) )

        win_prefs = self.app.prefs.getWindow()

        super().__init__()
        self.setWindowTitle( title )
        self.setWindowIcon( wb_git_images.getQIcon( 'wb.png' ) )

        # list of all the WbActionEnableState for the menus and toolbars
        self.__enable_state_manager = WbActionEnableStateManager( app )

        self.icon_size = QtCore.QSize( 32, 32 )

        self.__setupMenuBar()
        self.__setupToolBar()
        self.__setupStatusBar()

        self.__setupTreeContextMenu()
        self.__setupTableContextMenu()

        if win_prefs.getFramePosition() is not None:
            self.move( *win_prefs.getFramePosition() )

        self.resize( *win_prefs.getFrameSize() )

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

        # layout widgets in window
        self.v_split = QtWidgets.QSplitter()
        self.v_split.setOrientation( QtCore.Qt.Vertical )

        self.setCentralWidget( self.v_split )

        self.h_split = QtWidgets.QSplitter( self.v_split )
        self.h_split.setOrientation( QtCore.Qt.Horizontal )

        self.v_split_table = QtWidgets.QSplitter()
        self.v_split_table.setOrientation( QtCore.Qt.Vertical )

        self.h_filter_widget = QtWidgets.QWidget( self.v_split )
        self.h_filter_layout = QtWidgets.QHBoxLayout()

        self.h_filter_layout.addWidget( QtWidgets.QLabel( T_('Filter:') ) )
        self.h_filter_layout.addWidget( self.filter_text )

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
        # set splitter position
        tree_size_ratio = 0.3
        width = sum( self.h_split.sizes() )
        tree_width = int( width * tree_size_ratio )
        table_width = width - tree_width
        self.h_split.setSizes( [tree_width, table_width] )

        self.updateActionEnabledStates()

        self.log.debug( 'Debug messages are enabled' )

        self.timer = None

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
        self.__enable_state_manager.update()

    def __setupMenuBar( self ):
        mb = self.menuBar()

        m = mb.addMenu( T_('&File') )
        self.__addMenu( m, T_('E&xit'), self.close, self.enablerEnabled )

        m = mb.addMenu( T_('F&older Actions') )
        self.__addMenu( m, T_('&Command Shell'), self.treeActionShell, self.enablerFolderExists, 'toolbar_images/terminal.png' )
        self.__addMenu( m, T_('&File Browser'), self.treeActionFileBrowse, self.enablerFolderExists, 'toolbar_images/file_browser.png' )

        m = mb.addMenu( T_('File &Actions') )
        self.__addMenu( m, T_('Edit'), self.tableActionEdit, self.enablerFilesExists, 'toolbar_images/edit.png' )
        self.__addMenu( m, T_('Open'), self.tableActionOpen, self.enablerFilesExists, 'toolbar_images/open.png' )

        m = mb.addMenu( T_('&Information') )
        self.__addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionGitDiffHeadVsWorking, self.enablerDiffHeadVsWorking, 'toolbar_images/diff.png' )
        self.__addMenu( m, T_('Diff Staged vs. Working'), self.treeTableActionGitDiffStagedVsWorking, self.enablerDiffStagedVsWorking, 'toolbar_images/diff.png' )
        self.__addMenu( m, T_('Diff HEAD vs. Staged'), self.treeTableActionGitDiffHeadVsStaged, self.enablerDiffHeadVsStaged, 'toolbar_images/diff.png' )

        m = mb.addMenu( T_('&Git Actions') )
        self.__addMenu( m, T_('Stage'), self.tableActionGitStage, self.enablerFilesStage, 'toolbar_images/include.png' )
        self.__addMenu( m, T_('Unstage'), self.tableActionGitUnstage, self.enablerFilesUnstage, 'toolbar_images/exclude.png' )
        self.__addMenu( m, T_('Revert'), self.tableActionGitRevert, self.enablerFilesRevert, 'toolbar_images/revert.png' )
        m.addSeparator()
        self.__addMenu( m, T_('Commit'), self.treeActionCommit, self.enablerCommit )

        menu_help = mb.addMenu( T_('&Help' ) )
        self.__addMenu( menu_help, T_("&About..."), self.appActionAbout, self.enablerEnabled )

    def __setupTreeContextMenu( self ):
        m = self.tree_context_menu = QtWidgets.QMenu( self )
        m.addSection( T_('Folder Actions') )
        self.__addMenu( m, T_('&Command Shell'), self.treeActionShell, self.enablerFolderExists, 'toolbar_images/terminal.png' )
        self.__addMenu( m, T_('&File Browser'), self.treeActionFileBrowse, self.enablerFolderExists, 'toolbar_images/file_browser.png' )

    def __setupTableContextMenu( self ):
        m = self.table_context_menu = QtWidgets.QMenu( self )

        m.addSection( T_('File Actions') )
        self.__addMenu( m, T_('Edit'), self.tableActionEdit, self.enablerFilesExists, 'toolbar_images/edit.png' )
        self.__addMenu( m, T_('Open'), self.tableActionOpen, self.enablerFilesExists, 'toolbar_images/open.png' )

        m.addSection( T_('Diff') )
        self.__addMenu( m, T_('Diff HEAD vs. Working'), self.treeTableActionGitDiffHeadVsWorking, self.enablerDiffHeadVsWorking, 'toolbar_images/diff.png' )
        self.__addMenu( m, T_('Diff Staged vs. Working'), self.treeTableActionGitDiffStagedVsWorking, self.enablerDiffStagedVsWorking, 'toolbar_images/diff.png' )
        self.__addMenu( m, T_('Diff HEAD vs. Staged'), self.treeTableActionGitDiffHeadVsWorking, self.enablerDiffHeadVsStaged, 'toolbar_images/diff.png' )

        m.addSection( T_('Git Actions') )
        self.__addMenu( m, T_('Stage'), self.tableActionGitStage, self.enablerFilesStage, 'toolbar_images/include.png' )
        self.__addMenu( m, T_('Unstage'), self.tableActionGitUnstage, self.enablerFilesUnstage, 'toolbar_images/exclude.png' )
        self.__addMenu( m, T_('Revert'), self.tableActionGitRevert, self.enablerFilesRevert, 'toolbar_images/revert.png' )

    def __addMenu( self, menu, name, handler, enabler, icon_name=None ):
        if icon_name is None:
            action = menu.addAction( name )
        else:
            icon = wb_git_images.getQIcon( icon_name )
            action = menu.addAction( icon, name )

        action.triggered.connect( handler )

        self.__enable_state_manager.add( action, enabler )

    def __setupToolBar( self ):
        style = self.style()

        t = self.tool_bar_tree = self.__addToolBar( T_('tree') )
        self.__addTool( t, T_('Command Shell'), self.treeActionShell, self.enablerFolderExists, 'toolbar_images/terminal.png' )
        self.__addTool( t, T_('File Browser'), self.treeActionFileBrowse, self.enablerFolderExists, 'toolbar_images/file_browser.png' )

        t = self.tool_bar_table = self.__addToolBar( T_('table') )
        self.__addTool( t, T_('Edit'), self.tableActionEdit, self.enablerFilesExists, 'toolbar_images/edit.png' )
        self.__addTool( t, T_('Open'), self.tableActionOpen, self.enablerFilesExists, 'toolbar_images/open.png' )

        t = self.tool_bar_git_state = self.__addToolBar( T_('git state') )
        self.__addTool( t, T_('Stage'), self.tableActionGitStage, self.enablerFilesStage, 'toolbar_images/include.png' )
        self.__addTool( t, T_('Unstage'), self.tableActionGitUnstage, self.enablerFilesUnstage, 'toolbar_images/exclude.png' )
        self.__addTool( t, T_('Revert'), self.tableActionGitRevert, self.enablerFilesRevert, 'toolbar_images/revert.png' )
        t.addSeparator()
        self.__addTool( t, T_('Commit'), self.treeActionCommit, self.enablerCommit )

        t = self.tool_bar_git_info = self.__addToolBar( T_('git info') )
        self.__addTool( t, T_('Diff'), self.treeTableActionGitDiffSmart, self.enablerDiffSmart, 'toolbar_images/diff.png' )

    def __addToolBar( self, name ):
        bar = self.addToolBar( name )
        bar.setIconSize( self.icon_size )
        return bar

    def __addTool( self, bar, name, handler, enabler, icon_name=None ):
        if icon_name is None:
            action = bar.addAction( name )

        else:
            icon = wb_git_images.getQIcon( icon_name )
            action = bar.addAction( icon, name )

        action.triggered.connect( handler )
        self.__enable_state_manager.add( action, enabler )

    def __setupStatusBar( self ):
        s = self.statusBar()

        self.status_message = QtWidgets.QLabel()
        s.addWidget( self.status_message )

    #------------------------------------------------------------
    #
    #   Enabler handlers
    #
    #------------------------------------------------------------
    def enablerEnabled( self, cache ):
        return True

    def enablerFolderExists( self, cache ):
        key = '__treeSelectedAbsoluteFolder'
        if key not in cache:
            cache[ key ] = self.__treeSelectedAbsoluteFolder()

        return cache[ key ] is not None

    def enablerFilesExists( self, cache ):
        key = 'enablerFilesExists'
        if key not in cache:
            cache[ key ] = self.__tableSelectedExistingFiles()

        return len( cache[ key ] ) > 0

    def enablerFilesStage( self, cache ):
        key = 'enablerFilesStage'
        if key not in cache:
            with_status = (pygit2.GIT_STATUS_WT_MODIFIED|pygit2.GIT_STATUS_WT_NEW|pygit2.GIT_STATUS_WT_DELETED)
            cache[ key ] = self.__tableSelectedWithStatus( with_status, 0 )

        return cache[ key ]

    def enablerFilesUnstage( self, cache ):
        key = 'enablerFilesUnstage'
        if key not in cache:
            with_status = pygit2.GIT_STATUS_INDEX_MODIFIED|pygit2.GIT_STATUS_INDEX_NEW|pygit2.GIT_STATUS_INDEX_DELETED
            cache[ key ] = self.__tableSelectedWithStatus( with_status, 0 )

        return cache[ key ]

    def enablerFilesRevert( self, cache ):
        key = 'enablerFilesRevert'
        if key not in cache:
            with_status = pygit2.GIT_STATUS_WT_MODIFIED|pygit2.GIT_STATUS_WT_DELETED
            without_status = pygit2.GIT_STATUS_INDEX_MODIFIED
            cache[ key ] = self.__tableSelectedWithStatus( with_status, without_status )

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

    def __enablerTableSelectedDiffObjects( self, cache ):
        key = '__enablerTableSelectedDiffObjects'
        if key not in cache:
            cache[ key ] = self.__tableSelectedDiffObjects()

        return cache[ key ]

    def __enablerDiff( self, cache, key, predicate ):
        if key not in cache:
            focus = self.__enablerFocusWidget( cache )
            if focus == 'tree':
                cache[ key ] = True

            elif focus == 'table':
                # make sure all the selected entries is modified
                all_diff_objects = self.__enablerTableSelectedDiffObjects( cache )
                enable = True
                for obj in all_diff_objects:
                    if not predicate( obj ):
                        enable = False
                        break

                cache[ key ] = enable

            else:
                cache[ key ] = False

        return cache[ key ]

    def enablerDiffHeadVsWorking( self, cache ):
        return self.__enablerDiff( cache, 'enablerDiffHeadVsWorking', wb_git_project.WbGitDiffObjects.canDiffHeadVsWorking )

    def enablerDiffStagedVsWorking( self, cache ):
        return self.__enablerDiff( cache, 'enablerDiffStagedVsWorking', wb_git_project.WbGitDiffObjects.canDiffStagedVsWorking )

    def enablerDiffHeadVsStaged( self, cache ):
        return self.__enablerDiff( cache, 'enablerDiffHeadVsStaged', wb_git_project.WbGitDiffObjects.canDiffHeadVsStaged )

    def enablerDiffSmart( self, cache ):
        key = 'enablerDiffSmart'
        if key not in cache:
            focus = self.__enablerFocusWidget( cache )
            if focus == 'tree':
                cache[ key ] = True

            elif focus == 'table':
                # make sure all the selected entries is modified
                all_diff_objects = self.__enablerTableSelectedDiffObjects( cache )
                enable = True
                for obj in all_diff_objects:
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

            staged_status = pygit2.GIT_STATUS_INDEX_MODIFIED|pygit2.GIT_STATUS_INDEX_NEW|pygit2.GIT_STATUS_INDEX_DELETED

            can_commit = False
            for status in git_project.status.values():
                if (status&staged_status) != 0:
                    can_commit = True
                    break

            cache[ key ] = can_commit

        return cache[ key ]

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

    def moveEvent( self, event ):
        self.app.prefs.getWindow().setFramePosition( event.pos().x(), event.pos().y() )

    def resizeEvent( self, event ):
        self.app.prefs.getWindow().setFrameSize( event.size().width(), event.size().height() )

    def closeEvent( self, event ):
        self.app.writePreferences()

    #------------------------------------------------------------
    #
    # app actions
    #
    #------------------------------------------------------------
    def appActionPreferences( self ):
        pref_dialog = wb_git_preferences_dialog.PreferencesDialog( self, self.app )
        rc = pref_dialog.exec_()
        if rc == QtWidgets.QDialog.Accepted:
            self.app.writePreferences()
            self.newPreferences()

    def appActionAbout( self ):
        from PyQt5 import Qt
        all_about_info = []
        all_about_info.append( T_("%s %d.%d.%d-%d") %
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
            self.app.writePreferences()

        if close:
            self.close()

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

    #------------------------------------------------------------
    #
    # tree actions
    #
    #------------------------------------------------------------
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

        all_staged_files = []
        can_commit = False
        for filename, status in git_project.status.items():
            if (status&pygit2.GIT_STATUS_INDEX_NEW) != 0:
                all_staged_files.append( (T_('new file'), filename) )

            elif (status&pygit2.GIT_STATUS_INDEX_MODIFIED) != 0:
                all_staged_files.append( (T_('modified'), filename) )

            elif (status&pygit2.GIT_STATUS_INDEX_DELETED) != 0:
                all_staged_files.append( (T_('deleted'), filename) )

        dialog = wb_git_commit_dialog.WbGitCommitDialog(
                    self.app, self,
                    all_staged_files,
                    T_('Commit %s') % (git_project.projectName(),) )
        if dialog.exec_():
            git_project.cmdCommit( dialog.getMessage() )

            # take account of the change
            self.tree_model.refreshTree()

            # sort filter is now invalid
            self.table_sortfilter.invalidate()

            # enabled states will have changed
            self.updateActionEnabledStates()

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

    def __tableSelectedDiffObjects( self ):
        folder_path = self.__treeSelectedAbsoluteFolder()
        if folder_path is None:
            return []

        all_names = self.__tableSelectedFiles()
        if len(all_names) == 0:
            return []

        git_project = self.__treeSelectedGitProject()

        relative_folder = self.__treeSelectedRelativeFolder()

        return [git_project.getDiffObjects( relative_folder / name ) for name in all_names]

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

    def __actionGitStage( self, git_project, filename ):
        git_project.cmdStage( filename )

    def __actionGitUnStage( self, git_project, filename ):
        git_project.cmdUnstage( 'HEAD', filename, pygit2.GIT_RESET_MIXED )

    def __actionGitRevert( self, git_project, filename ):
        git_project.cmdRevert( 'HEAD', filename )

    def __actionGitDiffSmart( self, git_project, filename ):
        diff_objects = git_project.getDiffObjects( filename )

        if diff_objects.canDiffStagedVsWorking():
            self.__actionGitDiffStagedVsWorking( git_project, filename )

        elif diff_objects.canDiffHeadVsStaged():
            self.__actionGitDiffHeadVsStaged( git_project, filename )

        elif diff_objects.canDiffHeadVsWorking():
            self.__actionGitDiffHeadVsWorking( git_project, filename )

    def __actionGitDiffHeadVsWorking( self, git_project, filename ):
        diff_objects = git_project.getDiffObjects( filename )

        text = diff_objects.diffUnified( diff_objects.diff_head, diff_objects.diff_working )
        title = 'Diff HEAD vs. Work %s' % (filename,)

        window = wb_diff_view.WbDiffView( self.app, self, title, wb_git_images.getQIcon( 'wb.png' ) )
        window.setUnifiedDiffText( text )
        window.show()

    def __actionGitDiffStagedVsWorking( self, git_project, filename ):
        diff_objects = git_project.getDiffObjects( filename )

        text = diff_objects.diffUnified( diff_objects.diff_staged, diff_objects.diff_working )
        title = 'Diff Staged vs. Work %s' % (filename,)

        window = wb_diff_view.WbDiffView( self.app, self, title, wb_git_images.getQIcon( 'wb.png' ) )
        window.setUnifiedDiffText( text )
        window.show()

        self.all_diff_windows.append( window )

    def __actionGitDiffHeadVsStaged( self, git_project, filename ):
        diff_objects = git_project.getDiffObjects( filename )

        text = diff_objects.diffUnified( diff_objects.diff_head, diff_objects.diff_staged )
        title = 'Diff HEAD vs. Staged %s' % (filename,)

        window = wb_diff_view.WbDiffView( self.app, self, title, wb_git_images.getQIcon( 'wb.png' ) )
        window.setUnifiedDiffText( text )
        window.show()

    def __areYouSureAlways( self, all_filenames ):
        return True

    def __areYouSureRevert( self, all_filenames ):
        default_button = QtWidgets.QMessageBox.No

        title = 'Confirm Revert'
        all_parts = ['Are you sure you wish to revert:']
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

class WbActionEnableStateManager:
    def __init__( self, app ):
        self._debug = app._debugMainWindow

        self.__all_action_enablers = []

        self.__update_running = False

    def add( self, action, enable_handler ):
        self.__all_action_enablers.append( WbActionEnableState( action, enable_handler ) )

    def update( self ):
        if self.__update_running:
            return

        self.__update_running = True
        self._debug( 'WbActionEnableState.update running' )

        # use a cache to avoid calling state queries more then once on any one update
        cache = {}
        for enabler in self.__all_action_enablers:
            enabler.setEnableState( cache )

        self._debug( 'WbActionEnableState.update done' )
        self.__update_running = False

class WbActionEnableState:
    def __init__( self, action, enable_handler ):
        self.action = action
        self.enable_handler = enable_handler

    def setEnableState( self, cache ):
        self.action.setEnabled( self.enable_handler( cache ) )
