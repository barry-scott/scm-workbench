'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_table_model.py

'''
from PyQt6 import QtCore

import wb_scm_table_model
import wb_shell_commands
import wb_table_view

import wb_background_thread

from wb_background_thread import thread_switcher

class WbScmTableView(wb_table_view.WbTableView):
    def __init__( self, app, main_window ):
        self.app = app
        self.main_window = main_window

        self.debugLog = main_window.debugLog

        super().__init__()

        self.all_visible_columns = None

        # short cut keys in the table view
        self.table_keys_edit = ('\r', 'e', 'E')
        self.table_keys_open = ('o', 'O')

        self.all_table_keys = []
        self.all_table_keys.extend( self.table_keys_edit )
        self.all_table_keys.extend( self.table_keys_open )

        self.table_model = wb_scm_table_model.WbScmTableModel( self.app )

        self.table_sortfilter = wb_scm_table_model.WbScmTableSortFilter( self.app )
        self.table_sortfilter.setSourceModel( self.table_model )
        # does this hurt performance?
        self.table_sortfilter.setDynamicSortFilter( True )

        self.table_sort_column = self.table_model.col_status
        self.table_sort_order = QtCore.Qt.SortOrder.AscendingOrder

        # setModel triggers a selectionChanged event
        self.setModel( self.table_sortfilter )

        # allow Tab/Shift-Tab to move between tree/filter/table and log widgets
        self.setTabKeyNavigation( False )

        # set sort params
        self.sortByColumn( self.table_sort_column, self.table_sort_order )
        # and enable to apply
        self.setSortingEnabled( True )

        # always select a whole row
        self.setSelectionBehavior( self.SelectRows )
        self.doubleClicked.connect( self.tableDoubleClicked )

        # connect up signals
        self.horizontalHeader().sectionClicked.connect( self.tableHeaderClicked )
        self.customContextMenuRequested.connect( self.tableContextMenu )
        self.setContextMenuPolicy( QtCore.Qt.ContextMenuPolicy.CustomContextMenu )

        # after Qt 5.9.2 the column widths get reset before being shown
        self.setTableAllColumnWidths()

    def completeInit( self ):
        self.setTableAllColumnWidths()

    def setTableAllColumnWidths( self ):
        # size columns
        em = self.fontMetrics().width( 'm' )
        self.setColumnWidth( self.table_model.col_include, em*4 )
        self.setColumnWidth( self.table_model.col_staged, em*4 )
        self.setColumnWidth( self.table_model.col_status, em*4 )
        self.setColumnWidth( self.table_model.col_name, em*32 )
        self.setColumnWidth( self.table_model.col_date, em*20 )
        self.setColumnWidth( self.table_model.col_type, em*6 )

    def setFilterText( self, text ):
        # setting the filter text some times has the side effect of
        # showing all columns. This is assumed to be a bug in Qt.
        self.table_sortfilter.setFilterText( text )

        # force the column visibity incase it was overrinned by setFilterText.
        self.applyVisibleColumns()

    def focusInEvent( self, event ):
        super().focusInEvent( event )

        self.main_window.setFocusIsIn( 'table' )

    def setVisibleColumns( self, all_visible_columns ):
        self.all_visible_columns = all_visible_columns
        self.applyVisibleColumns()

    def applyVisibleColumns( self ):
        for col in range( self.table_model.col_num_columns ):
            self.setColumnHidden( col, col not in self.all_visible_columns )

    def tableContextMenu( self, pos ):
        self.debugLog( 'tableContextMenu( %r )' % (pos,) )
        global_pos = self.viewport().mapToGlobal( pos )

        self.main_window.tableContextMenu( global_pos )

    def setShowControlledAndChangedFiles( self, state ):
        self.table_sortfilter.setShowControlledAndChangedFiles( state )

    def setShowControlledAndNotChangedFiles( self, state ):
        self.table_sortfilter.setShowControlledAndNotChangedFiles( state )

    def setShowUncontrolledFiles( self, state ):
        self.table_sortfilter.setShowUncontrolledFiles( state )

    def setShowIgnoredFiles( self, state ):
        self.table_sortfilter.setShowIgnoredFiles( state )

    # ------------------------------------------------------------
    def checkerShowControlledAndChangedFiles( self ):
        return self.table_sortfilter.show_controlled_and_changed

    def checkerShowControlledAndNotChangedFiles( self ):
        return self.table_sortfilter.show_controlled_and_not_changed

    def checkerShowUncontrolledFiles( self ):
        return self.table_sortfilter.show_uncontrolled

    def checkerShowIgnoredFiles( self ):
        return self.table_sortfilter.show_ignored

    # ------------------------------------------------------------
    def setIncludedFilesSet( self, all_included_files ):
        self.table_model.setIncludedFilesSet( all_included_files )

    def setScmProjectTreeNode( self, tree_node ):
        self.table_model.setScmProjectTreeNode( tree_node )

    def selectedScmProject( self ):
        scm_project_tree_node = self.table_model.selectedScmProjectTreeNode()
        if scm_project_tree_node is None:
            return None

        return scm_project_tree_node.project

    def selectedAbsoluteFolder( self ):
        scm_project_tree_node = self.table_model.selectedScmProjectTreeNode()
        if scm_project_tree_node is None:
            return None

        folder_path = scm_project_tree_node.absolutePath()

        if not folder_path.exists():
            return None

        return folder_path

    def selectedRelativeFolder( self ):
        scm_project_tree_node = self.table_model.selectedScmProjectTreeNode()
        if scm_project_tree_node is None:
            return None

        return scm_project_tree_node.relativePath()

    def selectedAllFileStates( self ):
        all_names = self.tableSelectedFiles()

        scm_project = self.selectedScmProject()
        relative_folder = self.selectedRelativeFolder()

        # sometimes the selection is no longer in the projects file state
        return [scm_project.getFileState( relative_folder / name )
                for name in all_names
                if scm_project.hasFileState( relative_folder / name )]

    def tableActionViewRepo( self, execute_function, are_you_sure_function=None, finalise_function=None ):
        all_filenames = self.__tableActionViewRepoPrep( are_you_sure_function )
        if len(all_filenames) > 0:
            scm_project = self.selectedScmProject()

            for filename in all_filenames:
                execute_function( scm_project, filename )

            if finalise_function is not None:
                finalise_function( scm_project )

    # like tableActionViewRepo but uses yield for use with a thread switcher
    @thread_switcher
    def tableActionViewRepo_Bg( self, execute_function, are_you_sure_function=None, finalise_function=None ):
        self.debugLog( 'tableActionViewRepo_Bg start' )
        all_filenames = self.__tableActionViewRepoPrep( are_you_sure_function )

        if len(all_filenames) > 0:
            scm_project = self.selectedScmProject()

            for filename in all_filenames:
                if wb_background_thread.requiresThreadSwitcher( execute_function ):
                    self.debugLog( 'tableActionViewRepo_Bg exec yield from  %r' % (execute_function,) )
                    yield from execute_function( scm_project, filename )

                else:
                    self.debugLog( 'tableActionViewRepo_Bg exec call %r( %r, %r )' % (execute_function, scm_project, filename) )
                    execute_function( scm_project, filename )

            if finalise_function is not None:
                if wb_background_thread.requiresThreadSwitcher( finalise_function ):
                    self.debugLog( 'tableActionViewRepo_Bg fin yield from %r' % (finalise_function,) )
                    yield from finalise_function( scm_project )

                else:
                    self.debugLog( 'tableActionViewRepo_Bg fin call %r' % (finalise_function,) )
                    finalise_function( scm_project )

        self.debugLog( 'tableActionViewRepo_Bg done' )

    def __tableActionViewRepoPrep( self, are_you_sure_function ):
        folder_path = self.selectedAbsoluteFolder()
        if folder_path is None:
            return []

        all_names = self.tableSelectedFiles()
        if len(all_names) == 0:
            return []

        relative_folder = self.selectedRelativeFolder()

        all_filenames = [relative_folder / name for name in all_names]

        if( are_you_sure_function is not None
        and not are_you_sure_function( all_filenames ) ):
            return []

        return all_filenames

    def enablerTableFilesExists( self ):
        return len( self._tableSelectedExistingFiles() ) > 0

    def tableHeaderClicked( self, column ):
        if column == self.table_sort_column:
            if self.table_sort_order == QtCore.Qt.SortOrder.DescendingOrder:
                self.table_sort_order = QtCore.Qt.SortOrder.AscendingOrder
            else:
                self.table_sort_order = QtCore.Qt.SortOrder.DescendingOrder

        else:
            self.table_sort_column = column
            self.table_sort_order = QtCore.Qt.SortOrder.AscendingOrder

        self.sortByColumn( self.table_sort_column, self.table_sort_order )

    def tableKeyHandler( self, key ):
        if key in self.table_keys_edit:
            self.tableActionEdit()

        elif key in self.table_keys_open:
            self.tableActionOpen()

    def tableDoubleClicked( self, index ):
        self.tableActionEdit()

    def tableActionOpen( self ):
        all_filenames = self._tableSelectedExistingFiles()
        if len(all_filenames) > 0:
            wb_shell_commands.shellOpen( self.app, self.table_model.absoluteNodePath(), all_filenames )

    def tableActionEdit( self ):
        all_filenames = self._tableSelectedExistingFiles()
        if len(all_filenames) > 0:
            wb_shell_commands.editFile( self.app, self.table_model.absoluteNodePath(), all_filenames )

    def _tableSelectedExistingFiles( self ):
        folder_path = self.table_model.absoluteNodePath()
        if folder_path is None:
            return []

        all_filenames = [folder_path / name for name in self.tableSelectedFiles()]
        all_existing_filenames = [filename for filename in all_filenames if filename.exists()]
        return all_existing_filenames

    def tableSelectedFiles( self ):
        return [index.data( QtCore.Qt.ItemDataRole.UserRole ).name
                    for index in self.selectedIndexes()
                    if index.column() == self.table_model.col_name]

    def selectionChanged( self, selected, deselected ):
        self.debugLog( 'WbTableView.selectionChanged()' )

        self.main_window.updateActionEnabledStates()

        # allow the table to redraw the selected row highlights
        super().selectionChanged( selected, deselected )

    def keyPressEvent( self, event ):
        text = event.text()
        if text != '' and text in self.all_table_keys:
            self.tableKeyHandler( text )

        else:
            super().keyPressEvent( event )

    def keyReleaseEvent( self, event ):
        text = event.text()

        if text != '' and text in self.all_table_keys:
            return

        else:
            super().keyReleaseEvent( event )
