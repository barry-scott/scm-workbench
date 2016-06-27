'''
 ====================================================================
 Copyright (c) 2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_scm_table_model.py

'''
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

import wb_scm_table_model
import wb_shell_commands

class WbScmTableView(QtWidgets.QTableView):
    def __init__( self, app, main_window ):
        self.app = app
        self.main_window = main_window

        self._debug = main_window._debug

        super().__init__()

        # short cut keys in the table view
        self.table_keys_edit = ['\r', 'e', 'E']
        self.table_keys_open = ['o', 'O']

        self.all_table_keys = []
        self.all_table_keys.extend( self.table_keys_edit )
        self.all_table_keys.extend( self.table_keys_open )

        self.table_model = wb_scm_table_model.WbScmTableModel( self.app )

        self.table_sortfilter = wb_scm_table_model.WbScmTableSortFilter( self.app )
        self.table_sortfilter.setSourceModel( self.table_model )
        self.table_sortfilter.setDynamicSortFilter( False )

        self.table_sort_column = self.table_model.col_status
        self.table_sort_order = QtCore.Qt.AscendingOrder

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
        self.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )

        # size columns
        char_width = 10
        self.setColumnWidth( self.table_model.col_staged, char_width*4 )
        self.setColumnWidth( self.table_model.col_status, char_width*4 )
        self.setColumnWidth( self.table_model.col_name, char_width*32 )
        self.setColumnWidth( self.table_model.col_date, char_width*16 )
        self.setColumnWidth( self.table_model.col_type, char_width*6 )

    def setScmProjectTreeNode( self, tree_node ):
        self.table_model.setScmProjectTreeNode( tree_node )

    def tableHeaderClicked( self, column ):
        if column == self.table_sort_column:
            if self.table_sort_order == QtCore.Qt.DescendingOrder:
                self.table_sort_order = QtCore.Qt.AscendingOrder
            else:
                self.table_sort_order = QtCore.Qt.DescendingOrder

        else:
            self.table_sort_column = column
            self.table_sort_order = QtCore.Qt.AscendingOrder

        self.sortByColumn( self.table_sort_column, self.table_sort_order )

    def tableKeyHandler( self, key ):
        if key in self.table_keys_edit:
            self.tableActionEdit()

        elif key in self.table_keys_open:
            self.tableActionOpen()

    def tableContextMenu( self, pos ):
        self._debug( 'tableContextMenu( %r )' % (pos,) )
        global_pos = self.viewport().mapToGlobal( pos )

        self.main_window.all_ui_components[ 'git' ].getTableContextMenu().exec_( global_pos )

    def tableDoubleClicked( self, index ):
        self.tableActionEdit()

    def tableActionOpen( self ):
        all_filenames = self.main_window._tableSelectedExistingFiles()
        if len(all_filenames) > 0:
            wb_shell_commands.ShellOpen( self.app, self.main_window._treeSelectedAbsoluteFolder(), all_filenames )

    def tableActionEdit( self ):
        all_filenames = self.main_window._tableSelectedExistingFiles()
        if len(all_filenames) > 0:
            wb_shell_commands.EditFile( self.app, self.main_window._treeSelectedAbsoluteFolder(), all_filenames )

    def selectionChanged( self, selected, deselected ):
        self._debug( 'WbTableView.selectionChanged()' )

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
